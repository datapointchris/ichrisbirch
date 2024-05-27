import logging
import os
import subprocess
import threading
import time
from typing import Any
from typing import Generator

import pytest
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.blocking import BlockingScheduler
from docker.models.containers import Container
from fastapi.testclient import TestClient
from flask.testing import FlaskClient
from flask_login import FlaskLoginClient
from sqlalchemy.schema import CreateSchema

import tests.util
from ichrisbirch import models
from ichrisbirch.api.main import create_api
from ichrisbirch.app.main import create_app
from ichrisbirch.config import get_settings
from ichrisbirch.database.sqlalchemy.base import Base
from ichrisbirch.database.sqlalchemy.session import get_sqlalchemy_session
from ichrisbirch.scheduler.main import get_jobstore
from tests import test_data

logger = logging.getLogger(__name__)
docker_logger = logging.getLogger('DOCKER')

settings = get_settings('testing')
logger.info(f"load settings from environment: {settings.ENVIRONMENT}")


@pytest.fixture(scope='module')
def test_api() -> Generator[TestClient, Any, None]:
    api = create_api(settings=settings)
    api.dependency_overrides[get_sqlalchemy_session] = tests.util.get_testing_session
    with TestClient(api) as client:
        yield client


@pytest.fixture(scope='module')
def test_app() -> Generator[FlaskClient, Any, None]:
    app = create_app(settings=settings)
    app.testing = True
    app.config.update({'TESTING': True})
    app.config.update({'WTF_CSRF_ENABLED': False})
    with app.test_client() as client:
        with app.app_context():
            client.delete_cookie('session')
            yield client


@pytest.fixture(scope='module')
def test_app_logged_in() -> Generator[FlaskClient, Any, None]:
    """Produces a test client with a regular user logged in."""
    app = create_app(settings=settings)
    app.testing = True
    app.config.update({'TESTING': True})
    app.config.update({'WTF_CSRF_ENABLED': False})
    app.test_client_class = FlaskLoginClient
    with tests.util.SessionTesting() as session:
        regular_user = session.get(models.User, 1)
    with app.test_client(user=regular_user) as client:
        with app.app_context():
            yield client


@pytest.fixture(scope='module')
def test_app_logged_in_admin() -> Generator[FlaskClient, Any, None]:
    """Produces a test client with a regular user logged in."""
    app = create_app(settings=settings)
    app.testing = True
    app.config.update({'TESTING': True})
    app.config.update({'WTF_CSRF_ENABLED': False})
    app.test_client_class = FlaskLoginClient
    with tests.util.SessionTesting() as session:
        admin_user = session.get(models.User, 3)
    with app.test_client(user=admin_user) as client:
        with app.app_context():
            yield client


@pytest.fixture(scope='module')
def test_jobstore() -> Generator[SQLAlchemyJobStore, Any, None]:
    yield get_jobstore(settings=settings)


@pytest.fixture(scope='function', autouse=True)
def create_drop_tables():
    """All tables are created and dropped for each test function.

    This is the easiest way to ensure a clean db each time a new test is run.
    """
    Base.metadata.create_all(tests.util.ENGINE)
    yield
    Base.metadata.drop_all(tests.util.ENGINE)


@pytest.fixture(scope='function')
def insert_jobs_in_test_scheduler():
    # Start Scheduler in its own thread to test the scheduler
    test_scheduler = BlockingScheduler()
    jobstore = SQLAlchemyJobStore(url=settings.sqlalchemy.db_uri)
    test_scheduler.add_jobstore(jobstore, alias='ichrisbirch', extend_existing=True)
    scheduler_thread = threading.Thread(target=test_scheduler.start, daemon=True)
    scheduler_thread.start()
    for job in test_data.scheduler.BASE_DATA:
        test_scheduler.add_job(**job.as_dict())
    try:
        yield
    finally:
        # Shutdown scheduler process and join thread to main thread
        test_scheduler.shutdown()
        scheduler_thread.join()


@pytest.fixture(scope='session', autouse=True)
def setup_test_environment():
    """Setup testing environment.

    => Get Docker client (will attempt to start Docker if not running)
    => Create Postgres Docker container
    => Create Postgres logs thread
    => Create schemas
    => Start Uvicorn API (FastAPI) subprocess
    => Start Gunicorn App (Flask) subprocess
    => Yield to test
    =>a create_tables_insert_data_drop_tables runs here
    =>b Function yields after inserting data to run test
    =>c Drop all tables after test completes
    => Control back to setup_test_environment
    => Stop Postgres container
    => Kill Postgres, Uvicorn, and Gunicorn threads
    """
    docker_client = tests.util.get_docker_client()
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
    postgres_container = tests.util.create_docker_container(client=docker_client, config=postgres_container_config)

    def stream_docker_container_logs(container: Container):
        for log in docker_client.logs(container=container.get('Id'), stream=True, follow=True):
            log = log.decode().strip()
            docker_logger.info(log)

    # Start Docker log stream in its own thread
    docker_log_thread = threading.Thread(
        target=stream_docker_container_logs,
        kwargs={'container': postgres_container},
    )

    # Start Postgres container in its own thread
    postgres_thread = threading.Thread(
        target=docker_client.start,
        kwargs={'container': postgres_container.get('Id')},
    )
    postgres_thread.start()
    # Allow Postgres time to start
    time.sleep(3)
    docker_log_thread.start()

    # Create Schemas
    # with next(tests.helpers.get_testing_session()) as session:
    with tests.util.SessionTesting() as session:
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

    # Copy current environment and set ENVIRONMENT to testing for subprocesses
    testing_env = os.environ | {'ENVIRONMENT': settings.ENVIRONMENT}

    # Start Uvicorn API (FastAPI) subprocess in its own thread (for testing APP, that needs an API response)
    # This is easier than mocking everything
    api_uvicorn_command = ' '.join(
        [
            'poetry run uvicorn ichrisbirch.wsgi_api:api',
            f'--host {settings.fastapi.host}',
            f'--port {settings.fastapi.port}',
            '--log-level debug',
        ]
    )
    api_uvicorn_process = subprocess.Popen(api_uvicorn_command.split(), env=testing_env)
    api_uvicorn_thread = threading.Thread(target=api_uvicorn_process.wait)
    api_uvicorn_thread.start()
    time.sleep(1)  # Allow Uvicorn FastAPI to start

    # Start Gunicorn App (Flask) subprocess in its own thread (for testing the frontend)
    app_gunicorn_command = ' '.join(
        [
            'poetry run gunicorn ichrisbirch.wsgi_app:app',
            f'--bind {settings.flask.host}:{settings.flask.port}',
            '--log-level DEBUG',
        ]
    )
    app_gunicorn_process = subprocess.Popen(app_gunicorn_command.split(), env=testing_env)
    app_gunicorn_thread = threading.Thread(target=app_gunicorn_process.wait)
    app_gunicorn_thread.start()
    time.sleep(1)  # Allow Flask to start

    try:
        yield  # hold on while all tests in session run
    finally:
        # No need to delete the database, as it is in a Docker container
        # Stop container and join thread to main thread
        docker_client.stop(container=postgres_container.get('Id'))
        postgres_thread.join()

        docker_log_thread.join()
        # Kill uvicorn process and join thread to main thread
        api_uvicorn_process.kill()
        api_uvicorn_thread.join()
        # Kill flask process and join thread to main thread
        app_gunicorn_process.kill()
        app_gunicorn_thread.join()
