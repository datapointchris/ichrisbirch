import logging
import subprocess
import threading
import time
from copy import deepcopy
from typing import Any
from typing import Generator

import docker
import pytest
from docker.errors import DockerException
from docker.models.containers import Container
from fastapi.testclient import TestClient
from flask.testing import FlaskClient
from flask_login import FlaskLoginClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateSchema

from ichrisbirch.api.main import create_api
from ichrisbirch.app.main import create_app
from ichrisbirch.config import get_settings
from ichrisbirch.database.sqlalchemy.base import Base
from ichrisbirch.database.sqlalchemy.session import get_sqlalchemy_session
from tests import testing_data

logger = logging.getLogger(__name__)

settings = get_settings('testing')
logger.info(f"load settings from environment: {settings.ENVIRONMENT}")

ENGINE = create_engine(settings.sqlalchemy.db_uri, echo=False, future=True)
TESTING_SESSION = sessionmaker(bind=ENGINE, autocommit=False, autoflush=True, future=True, expire_on_commit=False)


def create_docker_container(client: docker.APIClient, config: dict[str, Any]) -> Container:
    image = config.pop("image")
    try:
        client.pull(image)
        container = client.create_container(image, **config)
    except DockerException as e:
        message = f"Failed to CREATE Docker client: {e}"
        logger.error(message)
        try:
            client.remove_container(container=config.get("name"), force=True)
            container = client.create_container(image, **config)
        except DockerException as e:
            message = f"Failed to REMOVE and RECREATE Docker container: {e}"
            logger.error(message)
            pytest.exit(message)
    time.sleep(3)  # Must sleep to allow creation of detached Docker container
    # TODO: I don't think this works, need to see when logging is fixed
    for log in client.logs(container=container.get("Id"), stream=True):
        logger.info(log.strip())
    return container


def get_testing_session() -> Generator[Session, None, None]:
    session = TESTING_SESSION()
    try:
        yield session
    finally:
        session.close()


def get_test_data() -> list:
    all_test_data = []
    for data in (
        testing_data.autotasks.BASE_DATA,
        testing_data.boxes.BASE_DATA,
        testing_data.boxitems.BASE_DATA,
        testing_data.countdowns.BASE_DATA,
        testing_data.events.BASE_DATA,
        testing_data.tasks.BASE_DATA,
    ):
        all_test_data.extend(deepcopy(data))
    return all_test_data


@pytest.fixture(scope='session', autouse=True)
def setup_test_environment():
    try:
        docker_client = docker.APIClient(base_url='unix://var/run/docker.sock')
    except DockerException:
        # Docker is not running
        print('docker is not running, starting...')
        subprocess.run(['open', '-ga', 'docker'])
        subprocess.run(['sleep', '20'])
        print('docker started')
        # Try again, let failure surface in the next command if this was not the issue
        docker_client = docker.APIClient(base_url='unix://var/run/docker.sock')

    # Create Postgres Docker container
    postgres_docker_container = create_docker_container(
        docker_client,
        dict(
            image='postgres:14',
            name='postgres_testing',
            environment={
                'ENVIRONMENT': settings.ENVIRONMENT,
                'POSTGRES_USER': settings.postgres.username,
                'POSTGRES_PASSWORD': settings.postgres.password,
                'POSTGRES_DB': settings.postgres.database,
            },
            ports=[5432],
            # Bind to port 5434 on host machine, so that it doesn't conflict with local Postgres
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
    # Allow Postgres time to start
    time.sleep(3)

    # Create Schemas
    with next(get_testing_session()) as session:
        for schema_name in settings.DB_SCHEMAS:
            try:
                session.execute(CreateSchema(schema_name))
            except Exception as e:
                logger.error(f"Failed to create schema: {e}")
                debug_message = f"""Failed to create schema: {e}
                postgres_connection_string = {settings.sqlalchemy.db_uri}
                Connection Parameters:
                database_name = {session.bind.url.database}
                database_user = {session.bind.url.username}
                database_password = {session.bind.url.password}
                database_host = {session.bind.url.host}
                database_port = {session.bind.url.port}
                """
                pytest.exit(debug_message)
        session.commit()

    # Start Uvicorn API (FastAPI) subprocess in its own thread (for testing APP, that needs an API response)
    # This is easier than mocking everything
    uvicorn_api_command = ' '.join(
        [
            'poetry run uvicorn ichrisbirch.wsgi_api:api',
            f'--host {settings.fastapi.host}',
            f'--port {settings.fastapi.port}',
            '--log-level debug',
        ]
    )
    uvicorn_api_process = subprocess.Popen(uvicorn_api_command.split())
    uvicorn_api_thread = threading.Thread(target=uvicorn_api_process.wait)
    uvicorn_api_thread.start()
    time.sleep(1)  # Allow Uvicorn FastAPI to start

    # Start Gunicorn App (Flask) subprocess in its own thread (for testing the frontend)
    gunicorn_app_command = ' '.join(
        [
            'poetry run gunicorn ichrisbirch.wsgi_app:app',
            f'--bind {settings.flask.host}:{settings.flask.port}',
            '--log-level DEBUG',
        ]
    )
    gunicorn_app_process = subprocess.Popen(gunicorn_app_command.split())
    gunicorn_app_thread = threading.Thread(target=gunicorn_app_process.wait)
    gunicorn_app_thread.start()
    time.sleep(1)  # Allow Flask to start

    try:
        yield  # hold on while all tests in session run
    finally:
        # No need to delete the database, as it is in a Docker container
        # Stop container and join thread to main thread
        docker_client.stop(container=postgres_docker_container.get('Id'))
        postgres_thread.join()
        # Kill uvicorn process and join thread to main thread
        uvicorn_api_process.kill()
        uvicorn_api_thread.join()
        # Kill flask process and join thread to main thread
        gunicorn_app_process.kill()
        gunicorn_app_thread.join()


@pytest.fixture(scope='function', autouse=True)
def insert_test_data():
    """All tables are created and dropped for each test function.

    This is the easiest way to ensure a clean db each time a new test is run. Have to deep copy or else the instances
    are the same and persist through sessions.

    """

    Base.metadata.create_all(ENGINE)
    session = next(get_testing_session())
    session.add_all(get_test_data())
    session.commit()
    yield
    session.close()
    Base.metadata.drop_all(ENGINE)


@pytest.fixture(scope='module')
def test_api() -> Generator[TestClient, Any, None]:
    api = create_api(settings=settings)
    api.dependency_overrides[get_sqlalchemy_session] = get_testing_session
    with TestClient(api) as client:
        yield client


@pytest.fixture(scope='module')
def test_app() -> Generator[FlaskClient, Any, None]:
    app = create_app(settings=settings)
    app.testing = True
    app.config.update({'TESTING': True})
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture(scope='module')
def test_app_logged_in() -> Generator[FlaskClient, Any, None]:
    app = create_app(settings=settings)
    app.testing = True
    app.config.update({'TESTING': True})
    app.test_client_class = FlaskLoginClient
    with app.test_client() as client:
        with app.app_context():
            yield client
