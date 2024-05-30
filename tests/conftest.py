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
            # client.delete_cookie('session')
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
def create_and_drop_tables():
    """All tables are created and dropped for each test function.

    This is the easiest way to ensure a clean db each time a new test is run.
    """
    Base.metadata.create_all(tests.util.ENGINE)
    logger.info('created all tables')
    yield
    Base.metadata.drop_all(tests.util.ENGINE)
    logger.info('dropped all tables')


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

    => Get Docker client (will attempt to start Docker if not running) => Create Postgres Docker container => Create
    Postgres logs thread => Create schemas => Start Uvicorn API (FastAPI) subprocess => Start Gunicorn App (Flask)
    subprocess => Yield to test =>a create_tables_insert_data_drop_tables runs here =>b Function yields after inserting
    data to run test =>c Drop all tables after test completes => Control back to setup_test_environment => Stop Postgres
    container => Kill Postgres, Uvicorn, and Gunicorn threads
    """

    try:
        docker_client = tests.util.get_docker_client(logger=logger)
        postgres_container = tests.util.create_postgres_docker_container(client=docker_client)
        logger.info('created postgres docker container')
        postgres_container_id = postgres_container.get('Id')
        postgres_thread = threading.Thread(target=docker_client.start, kwargs={'container': postgres_container_id})
        postgres_thread.start()
        time.sleep(3)  # Allow Postgres in Docker to start
        logger.info('started postgres docker container thread')

        docker_log_thread = threading.Thread(
            target=tests.util.docker_logs, kwargs={'client': docker_client, 'container_id': postgres_container_id}
        )
        docker_log_thread.start()
        logger.info('started docker log stream thread')

        _create_database_schemas(schemas=settings.DB_SCHEMAS, session=tests.util.SessionTesting)
        logger.info('created database schemas')

        # Copy current environment and set ENVIRONMENT to testing for subprocesses
        testing_env = os.environ | {'ENVIRONMENT': 'testing'}

        api_uvicorn_process = _create_api_uvicorn_process(env=testing_env)
        api_uvicorn_thread = threading.Thread(target=api_uvicorn_process.wait)
        api_uvicorn_thread.start()
        time.sleep(2)  # Allow Uvicorn FastAPI to start
        logger.info('started api uvicorn process thread')

        app_gunicorn_process = _create_app_gunicorn_process(env=testing_env)
        app_gunicorn_thread = threading.Thread(target=app_gunicorn_process.wait)
        app_gunicorn_thread.start()
        time.sleep(2)  # Allow Flask to start
        logger.info('started app gunicorn process thread')

        yield  # hold on while all tests in session run

    except Exception as e:
        logger.error(f'failed to set up the test environment: {e}')

    finally:
        # No need to delete the database, as it is in a Docker container
        # Stop container and join thread to main thread
        logger.info(f'stopping postgres docker container: {postgres_container_id}')
        docker_client.stop(container=postgres_container_id)

        logger.info('stopping postgres docker thread')
        postgres_thread.join()

        logger.info('stopping docker logging thread')
        docker_log_thread.join()

        logger.info('stopping api uvicorn process')
        api_uvicorn_process.kill()

        logger.info('stopping api uvicorn thread')
        api_uvicorn_thread.join()

        logger.info('stopping app gunicorn process')
        app_gunicorn_process.kill()

        logger.info('stopping app gunicorn thread')
        app_gunicorn_thread.join()


def _create_database_schemas(schemas, session):
    with session() as session:
        for schema_name in schemas:
            try:
                session.execute(CreateSchema(schema_name))
                logger.debug(f'created schema {schema_name}')
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


def _create_api_uvicorn_process(env):
    """Start Uvicorn API (FastAPI) subprocess in its own thread This is easier than mocking everything."""
    api_uvicorn_command = ' '.join(
        [
            'poetry run uvicorn ichrisbirch.wsgi_api:api',
            f'--host {settings.fastapi.host}',
            f'--port {settings.fastapi.port}',
            '--log-level debug',
        ]
    )
    process = subprocess.Popen(api_uvicorn_command.split(), env=env)
    return process


def _create_app_gunicorn_process(env):
    """Start Gunicorn App (Flask) subprocess in its own thread."""
    app_gunicorn_command = ' '.join(
        [
            'poetry run gunicorn ichrisbirch.wsgi_app:app',
            f'--bind {settings.flask.host}:{settings.flask.port}',
            '--log-level DEBUG',
        ]
    )
    process = subprocess.Popen(app_gunicorn_command.split(), env=env)
    return process
