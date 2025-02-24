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
from flask_login import login_user
from sqlalchemy.schema import CreateSchema

import tests.util
from ichrisbirch import models
from ichrisbirch.api.endpoints.auth import get_admin_user
from ichrisbirch.api.endpoints.auth import get_current_user
from ichrisbirch.api.main import create_api
from ichrisbirch.app.main import create_app
from ichrisbirch.config import get_settings
from ichrisbirch.database.sqlalchemy.base import Base
from ichrisbirch.database.sqlalchemy.session import get_sqlalchemy_session
from ichrisbirch.scheduler.main import get_jobstore
from tests import test_data

logger = logging.getLogger('tests.conftest')
logger.warning('<-- file imported')
testing_settings = get_settings('testing')


@pytest.fixture(scope='module')
def create_drop_tables():
    """Create all tables once per module."""
    Base.metadata.create_all(tests.util.ENGINE)
    logger.info('created all tables')
    yield
    Base.metadata.drop_all(tests.util.ENGINE)
    logger.info('dropped all tables')


@pytest.fixture(scope='module', autouse=True)
def insert_users_for_login(create_drop_tables):
    with tests.util.SessionTesting() as session:
        for user in tests.util.ALL_TEST_LOGIN_USERS:
            session.add(models.User(**user))
        session.commit()
        users = [tests.util.get_test_user(user) for user in tests.util.ALL_TEST_LOGIN_USERS]
        for user in users:
            logger.info(f'inserted in test db: {user.email}')
    yield


def base_testing_api():
    api = create_api(settings=testing_settings)
    api.dependency_overrides[get_sqlalchemy_session] = tests.util.get_testing_session
    return api


@pytest.fixture(scope='module')
def test_api():
    """Produces a test client with module scope."""
    with TestClient(base_testing_api()) as client:
        yield client


@pytest.fixture(scope='function')
def test_api_function():
    """Produces a test client with function scope."""
    with TestClient(base_testing_api()) as client:
        yield client


def base_testing_api_logged_in():
    api = base_testing_api()
    api_regular_user = tests.util.get_test_user(tests.util.TEST_LOGIN_API_REGULAR_USER)
    api.dependency_overrides[get_current_user] = lambda: api_regular_user
    logger.info(f'logged in user to test api: {api_regular_user.email}')
    return api


@pytest.fixture(scope='module')
def test_api_logged_in():
    """Produces a test client with module scope and user login."""
    with TestClient(base_testing_api_logged_in()) as client:
        yield client


@pytest.fixture(scope='function')
def test_api_logged_in_function():
    """Produces a test client with function scope and user login."""
    with TestClient(base_testing_api_logged_in()) as client:
        yield client


def base_testing_api_logged_in_admin():
    api = base_testing_api()
    api_admin_user = tests.util.get_test_user(tests.util.TEST_LOGIN_API_ADMIN_USER)
    api.dependency_overrides[get_admin_user] = lambda: api_admin_user
    logger.info(f'logged in admin user to test api: {api_admin_user.email}')
    return api


@pytest.fixture(scope='module')
def test_api_logged_in_admin():
    """Produces a test client with module scope and admin user login."""
    with TestClient(base_testing_api_logged_in_admin()) as client:
        yield client


@pytest.fixture(scope='function')
def test_api_logged_in_admin_function():
    """Produces a test client with function scope and admin user login."""
    with TestClient(base_testing_api_logged_in_admin()) as client:
        yield client


class APIHeadersFlaskClient(FlaskLoginClient):
    """A Flask test client that allows for setting API headers.

    This class sets the API headers for application login to the API.
    """

    def __init__(self, *args, **kwargs):
        self.api_headers = kwargs.pop('api_headers', {})
        super().__init__(*args, **kwargs)

    def open(self, *args, **kwargs):
        headers = kwargs.pop('headers', {})
        headers.update(self.api_headers)
        kwargs['headers'] = headers
        # kwargs['follow_redirects'] = True
        return super().open(*args, **kwargs)


def base_test_app() -> Generator[FlaskClient, Any, None]:
    """Base fixture for creating a test client."""
    app = create_app(settings=testing_settings)
    app.config.update({'TESTING': True})
    app.config.update({'WTF_CSRF_ENABLED': False})
    with app.test_request_context():
        with app.test_client() as client:
            yield client


@pytest.fixture(scope='module')
def test_app():
    """Produces a test client with module scope."""
    yield from base_test_app()


@pytest.fixture(scope='function')
def test_app_function():
    """Produces a test client with function scope."""
    yield from base_test_app()


def base_test_app_logged_in() -> Generator[FlaskClient, Any, None]:
    """Base fixture for creating a test client with a logged-in user.

    MUST set up the test_request_context first in order to have it to log in the user.
    """
    app = create_app(settings=testing_settings)
    app.config.update({'TESTING': True})
    app.config.update({'WTF_CSRF_ENABLED': False})
    app.test_client_class = APIHeadersFlaskClient
    user = tests.util.get_test_user(tests.util.TEST_LOGIN_REGULAR_USER)
    api_headers = {'X-Application-ID': testing_settings.flask.app_id, 'X-User-ID': user.get_id()}
    with app.test_request_context():
        login_user(user)
        logger.info(f'logged in user to test app: {user.email}: {user.get_id()}')
        with app.test_client(user=user, api_headers=api_headers) as client:
            yield client


@pytest.fixture(scope='module')
def test_app_logged_in():
    """Produces a test client with module scope and user login."""
    yield from base_test_app_logged_in()


@pytest.fixture(scope='function')
def test_app_logged_in_function():
    """Produces a test client with function scope and user login."""
    yield from base_test_app_logged_in()


def base_test_app_logged_in_admin() -> Generator[FlaskClient, Any, None]:
    """Base fixture for creating a test client with a logged-in admin user."""
    app = create_app(settings=testing_settings)
    app.config.update({'TESTING': True})
    app.config.update({'WTF_CSRF_ENABLED': False})
    app.test_client_class = APIHeadersFlaskClient
    admin = tests.util.get_test_user(tests.util.TEST_LOGIN_ADMIN_USER)
    api_headers = {'X-Application-ID': testing_settings.flask.app_id, 'X-User-ID': admin.get_id()}
    with app.test_request_context():
        login_user(admin)
        logger.info(f'logged in admin user to test app: {admin.email}: {admin.get_id()}')
        with app.test_client(user=admin, api_headers=api_headers) as client:
            yield client


@pytest.fixture(scope='module')
def test_app_logged_in_admin():
    """Produces a test client with module scope and admin user login."""
    yield from base_test_app_logged_in_admin()


@pytest.fixture(scope='function')
def test_app_logged_in_admin_function():
    """Produces a test client with function scope and admin user login."""
    yield from base_test_app_logged_in_admin()


@pytest.fixture(scope='module')
def test_jobstore() -> Generator[SQLAlchemyJobStore, Any, None]:
    yield get_jobstore(settings=testing_settings)


@pytest.fixture(scope='module')
def insert_jobs_in_test_scheduler():
    # Start Scheduler in its own thread to test the scheduler
    test_scheduler = BlockingScheduler()
    jobstore = SQLAlchemyJobStore(url=testing_settings.sqlalchemy.db_uri)
    test_scheduler.add_jobstore(jobstore, alias='ichrisbirch', extend_existing=True)
    scheduler_thread = threading.Thread(target=test_scheduler.start, daemon=True)
    scheduler_thread.start()
    for job in test_data.scheduler.BASE_DATA:
        test_scheduler.add_job(**job.as_dict())
        logger.info(f'added job: {job.id}')
    try:
        yield
    finally:
        # Shutdown scheduler process and join thread to main thread
        test_scheduler.shutdown()
        logger.info('scheduler was shutdown')
        scheduler_thread.join()


@pytest.fixture(scope='session', autouse=True)
def setup_test_environment():
    """Setup testing environment.

    - Get Docker client (will attempt to start Docker if not running)
    - Create Postgres Docker container
    - Create Postgres logs thread
    - Create schemas
    - Start Uvicorn API (FastAPI) subprocess
    - Start Gunicorn App (Flask) subprocess
    - Yield to test
    - - A create_tables_insert_data_drop_tables runs here
    - - B Function yields after inserting data to run test
    - - C Drop all tables after test completes
    - Control back to setup_test_environment
    - Stop Postgres container
    - Kill Postgres, Uvicorn, and Gunicorn threads
    """
    logger.warning('')
    logger.warning(f'{'='*30}>  STARTING TESTING  <{'='*30}')
    logger.warning('')
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

        _create_database_schemas(schemas=testing_settings.db_schemas, session=tests.util.SessionTesting)
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

    logger.warning('')
    logger.warning(f'{'='*30}>  TESTING FINISHED  <{'='*30}')
    logger.warning('')


def _create_database_schemas(schemas, session):
    with session() as session:
        for schema_name in schemas:
            try:
                session.execute(CreateSchema(schema_name))
                logger.info(f'created schema {schema_name}')
            except Exception as e:
                logger.error(f"Failed to create schema: {e}")
                debug_message = f"""Failed to create schema: {e}
                postgres_connection_string = {testing_settings.sqlalchemy.db_uri}
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
            f'--host {testing_settings.fastapi.host}',
            f'--port {testing_settings.fastapi.port}',
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
            f'--bind {testing_settings.flask.host}:{testing_settings.flask.port}',
            '--log-level DEBUG',
        ]
    )
    process = subprocess.Popen(app_gunicorn_command.split(), env=env)
    return process
