import logging
import subprocess
import threading
import time
from typing import Any
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from flask.testing import FlaskClient
from flask_login import FlaskLoginClient
from sqlalchemy.schema import CreateSchema

import tests.helpers
from ichrisbirch.api.main import create_api
from ichrisbirch.app.main import create_app
from ichrisbirch.config import get_settings
from ichrisbirch.database.sqlalchemy.base import Base
from ichrisbirch.database.sqlalchemy.session import get_sqlalchemy_session

logger = logging.getLogger(__name__)

settings = get_settings('testing')
logger.info(f"load settings from environment: {settings.ENVIRONMENT}")


@pytest.fixture(scope='module')
def test_api() -> Generator[TestClient, Any, None]:
    api = create_api(settings=settings)
    api.dependency_overrides[get_sqlalchemy_session] = tests.helpers.get_testing_session
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


@pytest.fixture(scope='function', autouse=True)
def create_tables_insert_data_drop_tables():
    """All tables are created and dropped for each test function.

    This is the easiest way to ensure a clean db each time a new test is run.

    """
    Base.metadata.create_all(tests.helpers.ENGINE)
    tests.helpers.insert_test_data()
    yield
    Base.metadata.drop_all(tests.helpers.ENGINE)


@pytest.fixture(scope='session', autouse=True)
def setup_test_environment():
    """Setup testing environment.

    1. Get Docker client (will attempt to start Docker if not running)
    2. Create Postgres Docker container
    3. Create schemas
    4. Start Uvicorn API (FastAPI) subprocess
    5. Start Gunicorn App (Flask) subprocess
    6. Yield to test
    6a. create_tables_insert_data_drop_tables runs here
    6b. Function yields after inserting data to run test
    6c. Drop all tables after test completes
    7. Control back to setup_test_environment
    8. Stop Postgres container
    9. Kill Postgres, Uvicorn, and Gunicorn threads

    """
    docker_client = tests.helpers.get_docker_client()
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
        host_config=docker_client.create_host_config(port_bindings={5432: 5434}, auto_remove=True),
        detach=True,
        labels=['testing'],
    )
    # Create Postgres Docker container
    postgres_container = tests.helpers.create_docker_container(client=docker_client, config=postgres_container_config)
    # Start Postgres container in its own thread
    postgres_thread = threading.Thread(
        target=docker_client.start,
        kwargs={'container': postgres_container.get('Id')},
    )
    postgres_thread.start()
    # Allow Postgres time to start
    time.sleep(3)

    # Create Schemas
    # with next(tests.helpers.get_testing_session()) as session:
    with tests.helpers.SessionTesting() as session:
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
        docker_client.stop(container=postgres_container.get('Id'))
        postgres_thread.join()
        # Kill uvicorn process and join thread to main thread
        uvicorn_api_process.kill()
        uvicorn_api_thread.join()
        # Kill flask process and join thread to main thread
        gunicorn_app_process.kill()
        gunicorn_app_thread.join()
