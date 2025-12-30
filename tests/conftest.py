"""Pytest configuration and fixtures.

This module provides pytest fixtures for all test modules, centralizing test setup and teardown. In the containerized approach, we rely on
environment-based configuration rather than overrides.
"""

import logging
import threading
from contextlib import contextmanager

import pytest
from apscheduler.schedulers.blocking import BlockingScheduler
from fastapi.testclient import TestClient
from flask_login import FlaskLoginClient
from flask_login import login_user
from sqlalchemy import select

from ichrisbirch import models
from ichrisbirch.api.endpoints import auth
from ichrisbirch.api.main import create_api
from ichrisbirch.app.main import create_app
from ichrisbirch.config import get_settings
from ichrisbirch.database.base import Base
from ichrisbirch.database.session import get_db_engine
from ichrisbirch.database.session import get_sqlalchemy_session
from ichrisbirch.scheduler.main import get_jobstore
from tests import test_data
from tests.environment import DockerComposeTestEnvironment
from tests.utils.database import create_session
from tests.utils.database import get_test_login_users
from tests.utils.database import get_test_runner_settings
from tests.utils.database import get_test_session
from tests.utils.database import get_test_user
from tests.utils.database import test_settings

logger = logging.getLogger(__name__)
logger.warning('<-- file imported')


@pytest.fixture(scope='session', autouse=True)
def setup_test_environment():
    logger.warning('')
    logger.warning(f'{"=" * 30}>  STARTING TESTING  <{"=" * 30}')
    logger.warning('')

    with DockerComposeTestEnvironment(test_settings, create_session) as test_env:
        logger.info('Docker Compose test environment is ready')
        yield test_env

    logger.warning('')
    logger.warning(f'{"=" * 30}>  TESTING FINISHED  <{"=" * 30}')
    logger.warning('')


@pytest.fixture(scope='module')
def create_drop_tables():
    engine = get_db_engine(test_settings)
    Base.metadata.create_all(engine)
    logger.info('created all tables')
    yield
    Base.metadata.drop_all(engine)
    logger.info('dropped all tables')


@pytest.fixture(scope='module', autouse=True)
def insert_users_for_login(create_drop_tables):
    """Ensure login users exist for this module (idempotent)."""
    with create_session(test_settings) as session:
        for user_data in get_test_login_users():
            existing = session.execute(select(models.User).where(models.User.email == user_data['email'])).scalar_one_or_none()
            if not existing:
                session.add(models.User(**user_data))
        session.commit()
        for user in session.query(models.User).all():
            logger.info(f'Login user ready: {user.email} with alt ID: {user.alternative_id}')
    yield


@pytest.fixture(scope='module')
def test_scheduler():
    """Insert jobs into test scheduler."""
    # Start Scheduler in its own thread or it will block the main thread
    test_scheduler = BlockingScheduler()
    test_jobstore = get_jobstore(test_settings)
    test_scheduler.add_jobstore(test_jobstore, alias=test_settings.sqlalchemy.database, extend_existing=True)
    scheduler_thread = threading.Thread(target=test_scheduler.start, daemon=True)
    logger.info('starting test scheduler thread')
    scheduler_thread.start()
    try:
        yield test_scheduler
    finally:
        test_scheduler.shutdown()
        logger.info('Scheduler was shutdown')
        scheduler_thread.join()


@pytest.fixture(scope='module')
def insert_test_jobs(test_scheduler):
    for job in test_data.scheduler.BASE_DATA:
        test_scheduler.add_job(**job.as_dict())
        logger.info(f'Added job: {job.id}')


@contextmanager
def create_test_api_client(login=False, admin=False):
    api = create_api(settings=test_settings)
    client = TestClient(api)

    api.dependency_overrides[get_sqlalchemy_session] = get_test_session
    api.dependency_overrides[get_settings] = get_test_runner_settings

    if login:
        email = 'testloginadmin@testadmin.com' if admin else 'testloginregular@testuser.com'
        user = get_test_user(email)
        api.dependency_overrides[auth.get_current_user] = lambda: user
        api.dependency_overrides[auth.get_current_user_or_none] = lambda: user
        # Only override get_admin_user if the user is actually an admin
        if admin:
            api.dependency_overrides[auth.get_admin_user] = lambda: user
        logger.info(f'Logged in {"admin" if admin else "regular"} user to test api: {user.email}')
    yield client


@pytest.fixture(scope='module')
def test_api():
    """Create test API client without overrides."""
    with create_test_api_client() as client:
        yield client


@pytest.fixture(scope='module')
def test_api_logged_in():
    """Create test API client with logged in user."""
    with create_test_api_client(login=True) as client:
        yield client


@pytest.fixture(scope='module')
def test_api_logged_in_admin():
    """Create test API client with logged in admin."""
    with create_test_api_client(login=True, admin=True) as client:
        yield client


class FlaskClientAPIHeaders(FlaskLoginClient):
    """A Flask test client that allows for setting API headers."""

    def __init__(self, *args, **kwargs):
        self.api_headers = kwargs.pop('api_headers', {})
        super().__init__(*args, **kwargs)

    def open(self, *args, **kwargs):
        headers = kwargs.pop('headers', {})
        headers.update(self.api_headers)
        kwargs['headers'] = headers
        return super().open(*args, **kwargs)


def create_test_app_base():
    """This is used for the test client and also for tests/wsgi_app.py for Gunicorn."""
    app = create_app(settings=test_settings)
    app.config.update({'TESTING': True, 'WTF_CSRF_ENABLED': False})
    return app


def create_test_app_client(login=False, admin=False):
    """Create a Flask test client with optional user login."""
    app = create_test_app_base()
    if login:
        app.test_client_class = FlaskClientAPIHeaders
        email = 'testloginadmin@testadmin.com' if admin else 'testloginregular@testuser.com'
        user = get_test_user(email)
        api_headers = {
            'X-Application-ID': test_settings.flask.app_id,
            'X-User-ID': user.get_id(),
            'X-Service-Key': test_settings.auth.internal_service_key,
        }
        with app.test_request_context():
            login_user(user)
            client = app.test_client(user=user, api_headers=api_headers)
            logger.info(f'Logged in {"admin" if admin else "user"} to test app: {user.email}: {user.get_id()}')
            return client
    return app.test_client()


@pytest.fixture(scope='module')
def test_app():
    """Create test Flask app client."""
    with create_test_app_client() as client:
        yield client


@pytest.fixture(scope='module')
def test_app_logged_in():
    """Create test Flask app client with logged in user."""
    with create_test_app_client(login=True) as client:
        yield client


@pytest.fixture(scope='module')
def test_app_logged_in_admin():
    """Create test Flask app client with logged in admin."""
    with create_test_app_client(login=True, admin=True) as client:
        yield client


@pytest.fixture(scope='function')
def test_app_function():
    with create_test_app_client() as client:
        yield client


@pytest.fixture(scope='function')
def test_app_logged_in_function():
    with create_test_app_client(login=True) as client:
        yield client


@pytest.fixture(scope='function')
def test_app_logged_in_admin_function():
    with create_test_app_client(login=True, admin=True) as client:
        yield client


@pytest.fixture(scope='function')
def test_api_function():
    with create_test_api_client() as client:
        yield client


@pytest.fixture(scope='function')
def test_api_logged_in_function():
    with create_test_api_client(login=True) as client:
        yield client


@pytest.fixture(scope='function')
def test_api_logged_in_admin_function():
    with create_test_api_client(login=True, admin=True) as client:
        yield client
