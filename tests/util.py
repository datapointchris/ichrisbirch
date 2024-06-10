import logging
import subprocess
import time
from copy import deepcopy
from typing import Any
from typing import Generator

import docker
import httpx
import pytest
from docker.errors import DockerException
from docker.models.containers import Container
from fastapi import status
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

import tests.test_data
from ichrisbirch.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings('testing')
logger.debug(f"load settings from environment: {settings.ENVIRONMENT}")


ENGINE = create_engine(
    settings.sqlalchemy.db_uri,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=5,
    connect_args={
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
)
SessionTesting = sessionmaker(bind=ENGINE, autocommit=False, autoflush=True, expire_on_commit=False)


def get_testing_session() -> Generator[Session, None, None]:
    session = SessionTesting()
    try:
        yield session
    finally:
        session.close()


def insert_test_data(*datasets) -> None:
    """Insert testing data for each endpoint.

    The data is manually added, must update when a new endpoint is added.
    deepcopy(data) is necessary or the tests will mutate the BASE_DATA
    and cause test failures

    Get only the data needed for each endpoint, speeds up tests a bunch.
    The tradeoff is a fixture must be created in each testing file

    Example (put at the top of each file using the testing data):

    ```python
    import tests.util


    @pytest.fixture(autouse=True)
    def insert_testing_data():
        tests.util.insert_test_data("tasks")
    ```
    """
    base_datasets = {
        'autotasks': tests.test_data.autotasks.BASE_DATA,
        'boxes': tests.test_data.boxes.BASE_DATA,
        'boxitems': tests.test_data.boxitems.BASE_DATA,
        'countdowns': tests.test_data.countdowns.BASE_DATA,
        'events': tests.test_data.events.BASE_DATA,
        'habits': tests.test_data.habits.BASE_DATA,
        'tasks': tests.test_data.tasks.BASE_DATA,
        'users': tests.test_data.users.BASE_DATA,
    }
    selected_datasets = [deepcopy(base_datasets[key]) for key in datasets if key in base_datasets]
    logger.debug(f'inserting testing dataset: {' '.join(f"'{d}'" for d in datasets)}')
    with SessionTesting() as session:
        for data in selected_datasets:
            session.add_all(data)
        session.commit()


def show_status_and_response(response: httpx.Response) -> dict[str, str]:
    """Convert status code to description and return response if any."""
    d = {}
    for attr in dir(status):
        code = attr.split('_')[1]
        d[int(code)] = attr
    try:
        content = response.json()
    except (httpx.DecodingError, TypeError) as e:
        logger.warning(f'error decoding response content: {e}')
        content = '<no response content>'

    return {d.get(response.status_code, 'UNKNOWN'): content}


def get_docker_client(logger: logging.Logger) -> docker.APIClient:
    try:
        return docker.APIClient(base_url='unix://var/run/docker.sock')
    except DockerException:
        logger.warning('docker is not running, starting...')
        subprocess.run(['open', '-ga', 'docker'])
        subprocess.run(['sleep', '20'])
        logger.info('docker started')
        # Try again, let failure surface in the next command if this was not the issue
        return docker.APIClient(base_url='unix://var/run/docker.sock')


def create_docker_container(client: docker.APIClient, config: dict[str, Any]) -> Container:
    image = config.pop("image")
    try:
        client.pull(image)
        container = client.create_container(image, **config)
    except DockerException as e:
        message = f"Failed to CREATE Docker container: {e}"
        logger.error(message)
        try:
            client.remove_container(container=config.get("name"), force=True)
            container = client.create_container(image, **config)
        except DockerException as e:
            message = f"Failed to REMOVE and RECREATE Docker container: {e}"
            logger.error(message)
            pytest.exit(message)
    time.sleep(3)  # Must sleep to allow creation of detached Docker container
    return container


def create_postgres_docker_container(client: docker.APIClient):
    postgres_container_config = dict(
        image='postgres:16',
        name='postgres_testing',
        environment={
            'ENVIRONMENT': settings.ENVIRONMENT,
            'POSTGRES_USER': settings.postgres.username,
            'POSTGRES_PASSWORD': settings.postgres.password,
            'POSTGRES_DB': settings.postgres.database,
        },
        ports=[5432],
        # Bind to port 5434 on host machine, so that it doesn't conflict with local Postgres
        host_config=client.create_host_config(port_bindings={5432: 5434}, auto_remove=True),
        detach=True,
        labels=['testing'],
    )
    postgres_container = create_docker_container(client=client, config=postgres_container_config)
    return postgres_container


def docker_logs(client: docker.APIClient, container_id: str):
    docker_logger = logging.getLogger('DOCKER')
    for log in client.logs(container=container_id, stream=True, follow=True):
        log = log.decode().strip()
        docker_logger.debug(log)
