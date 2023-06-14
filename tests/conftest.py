import logging
import subprocess
import threading
import time
from copy import deepcopy
from typing import Any, Generator

import docker
import pytest
from docker.errors import DockerException
from docker.models.containers import Container
from fastapi.testclient import TestClient
from flask.testing import FlaskClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.schema import CreateSchema

from ichrisbirch.api.main import create_api
from ichrisbirch.app.main import create_app
from ichrisbirch.config import get_settings
from ichrisbirch.database.sqlalchemy.base import Base
from ichrisbirch.database.sqlalchemy.session import sqlalchemy_session
from tests.testing_data.autotasks import BASE_DATA as AUTOTASK_BASE_DATA
from tests.testing_data.countdowns import BASE_DATA as COUNTDOWN_BASE_DATA
from tests.testing_data.tasks import BASE_DATA as TASK_BASE_DATA

settings = get_settings()
logger = logging.getLogger(__name__)

ENGINE = create_engine(settings.sqlalchemy.db_uri, echo=settings.sqlalchemy.echo, future=True)
SESSION_TESTING = sessionmaker(bind=ENGINE, autocommit=False, autoflush=True, future=True, expire_on_commit=False)


def create_docker_container(client: docker.APIClient, config: dict[str, Any]) -> Container:
    try:
        image = config.pop('image')
        client.pull(image)
        container = client.create_container(image, **config)
    except DockerException as e:
        message = f'Failed to RUN Docker client: {e}'
        logger.error(message)
        pytest.exit(message)
    time.sleep(3)  # Must sleep to allow creation of detached Docker container
    # TODO: I don't think this works, need to see when logging is fixed
    for log in client.logs(container=container.get('Id'), stream=True):
        print(log.strip())
        logging.info(log.strip())
    return container


def get_testing_session() -> Generator[Session, None, None]:
    try:
        session = SESSION_TESTING()
        yield session
    finally:
        session.close()


@pytest.fixture(scope='session', autouse=True)
def setup_test_environment():
    docker_client = docker.APIClient(base_url='unix://var/run/docker.sock')

    # Create Postgres Docker container
    postgres_docker_container = create_docker_container(
        docker_client,
        dict(
            image='postgres:14',
            name='postgres_testing',
            environment={'ENVIRONMENT': 'testing', 'POSTGRES_USER': 'postgres', 'POSTGRES_PASSWORD': 'postgres'},
            ports=[5432],
            host_config=docker_client.create_host_config(port_bindings={5432: 5434}, auto_remove=True),
            detach=True,
            labels=['testing'],
        ),
    )
    # Start Postgres container in its own thread
    postgres_thread = threading.Thread(
        target=docker_client.start,
        kwargs={'container': postgres_docker_container.get('Id')},
    )
    postgres_thread.start()
    time.sleep(3)  # Allow Postgres to start

    # Create Schemas
    with next(get_testing_session()) as session:
        for schema_name in settings.db_schemas:
            session.execute(CreateSchema(schema_name))
        session.commit()
        print('Schemas created')

    # Start Uvicorn FastAPI subprocess in its own thread (for testing APP, that needs an API response)
    # This is easier than mocking everything
    uvicorn_command = 'uvicorn ichrisbirch.api.main:create_api --factory --host localhost --port 5555 --log-level debug'
    uvicorn_process = subprocess.Popen(uvicorn_command.split())
    uvicorn_thread = threading.Thread(target=uvicorn_process.wait)
    uvicorn_thread.start()
    time.sleep(1)  # Allow Uvicorn FastAPI to start

    try:
        yield  # hold on while all tests in session run
    finally:
        # No need to delete the database, as it is in a Docker container
        # Stop container and join thread to main thread
        docker_client.stop(container=postgres_docker_container.get('Id'))
        postgres_thread.join()
        # Kill uvicorn process and join thread to main thread
        uvicorn_process.kill()
        uvicorn_thread.join()


@pytest.fixture(scope='function', autouse=True)
def insert_test_data():
    """All tables are created and dropped for each test function.
    This is the easiest way to ensure a clean db each time a new test is run.
    Have to deep copy or else the instances are the same and persist through sessions.
    TODO: [2023/06/14] - Find a better way to get this data than import of global variables and deepcopy.
    """
    all_test_data = deepcopy(AUTOTASK_BASE_DATA) + deepcopy(TASK_BASE_DATA) + deepcopy(COUNTDOWN_BASE_DATA)
    Base.metadata.create_all(ENGINE)
    session = next(get_testing_session())
    session.add_all(all_test_data)
    session.commit()
    yield
    session.close()
    Base.metadata.drop_all(ENGINE)


@pytest.fixture(scope='module')
def test_api() -> Generator[TestClient, Any, None]:
    api = create_api()
    api.dependency_overrides[sqlalchemy_session] = get_testing_session
    with TestClient(api) as client:
        yield client


@pytest.fixture(scope='module')
def test_app() -> Generator[FlaskClient, Any, None]:
    app = create_app()
    app.testing = True
    app.config.update({'TESTING': True})
    with app.test_client() as client:
        with app.app_context():
            yield client
