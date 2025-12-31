"""Pytest configuration and fixtures.

This module provides pytest fixtures for all test modules, centralizing test setup and teardown. In the containerized approach, we rely on
environment-based configuration rather than overrides.
"""

import contextlib
import logging
import threading
from contextlib import contextmanager

import pytest
from apscheduler.schedulers.blocking import BlockingScheduler
from fastapi.testclient import TestClient
from flask_login import FlaskLoginClient
from flask_login import login_user
from sqlalchemy import select
from sqlalchemy.orm import Session

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
from tests.factories import clear_factory_session
from tests.factories import set_factory_session
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


@pytest.fixture(scope='session')
def create_drop_tables(setup_test_environment):
    """Create all tables once at session start, drop at session end.

    This is session-scoped for performance - avoiding ~44 CREATE/DROP cycles.
    Individual test modules manage their own data via insert_test_data/delete_test_data.

    Note: We drop tables first to ensure a clean slate (removes leftover data
    from previous test runs when containers persist between sessions).
    """
    engine = get_db_engine(test_settings)
    Base.metadata.drop_all(engine)
    logger.info('dropped all tables (clean slate)')
    Base.metadata.create_all(engine)
    logger.info('created all tables (session scope)')
    yield
    Base.metadata.drop_all(engine)
    logger.info('dropped all tables (session scope)')


@pytest.fixture(scope='session', autouse=True)
def insert_users_for_login(create_drop_tables):
    """Ensure login users exist for the session (idempotent).

    Session-scoped for performance - runs once instead of ~44 times.
    """
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


SEQUENCES_TO_RESET = [
    'public.articles_id_seq',
    'public.autotasks_id_seq',
    'public.books_id_seq',
    'box_packing.boxes_id_seq',
    'box_packing.items_id_seq',
    'chat.chats_id_seq',
    'chat.messages_id_seq',
    'public.countdowns_id_seq',
    'public.events_id_seq',
    'habits.categories_id_seq',
    'habits.completed_id_seq',
    'habits.habits_id_seq',
    'public.money_wasted_id_seq',
    'public.tasks_id_seq',
]


def reset_sequences(engine):
    """Reset all sequences to 1 for consistent test isolation.

    Note: users_id_seq is NOT reset because login users (IDs 1-3) are session-scoped.
    """
    from sqlalchemy import text

    with engine.connect() as reset_conn:
        for seq in SEQUENCES_TO_RESET:
            with contextlib.suppress(Exception):
                reset_conn.execute(text(f'ALTER SEQUENCE {seq} RESTART WITH 1'))
        reset_conn.commit()


@pytest.fixture(scope='function')
def factory_session(create_drop_tables):
    """Provide a transactional SQLAlchemy session for factory_boy factories.

    Uses transaction isolation: all operations are wrapped in a transaction
    that is rolled back after the test, automatically cleaning up all data.
    Sequences are also reset to ensure consistent IDs for subsequent tests.

    Usage:
        def test_with_factories(factory_session):
            from tests.factories import TaskFactory
            task = TaskFactory(name='My Task', priority=10)
            assert task.id is not None
            # Data is automatically cleaned up after test via rollback
    """
    from tests.utils.database import clear_test_connection
    from tests.utils.database import set_test_connection

    engine = get_db_engine(test_settings)
    connection = engine.connect()
    transaction = connection.begin()

    # Configure the test connection for transactional isolation
    set_test_connection(connection)

    # Create session bound to this connection
    session = Session(bind=connection)

    # Configure factories to use this session
    set_factory_session(session)

    yield session

    # Cleanup: rollback transaction (undoes all changes)
    clear_factory_session()
    session.close()
    clear_test_connection()
    transaction.rollback()

    # Reset sequences since rollback doesn't affect sequences
    reset_sequences(engine)

    connection.close()


@contextmanager
def create_transactional_api_client(login=False, admin=False):
    """Create an API client with transaction-based isolation.

    All database operations (both factory data creation and API calls) participate
    in a single transaction that is rolled back after the test completes.

    Args:
        login: If True, authenticate as regular user
        admin: If True, authenticate as admin user (requires login=True to work)

    Yields:
        tuple: (TestClient, Session) - API client and transactional session
    """
    from tests.utils.database import clear_test_connection
    from tests.utils.database import get_transactional_session
    from tests.utils.database import set_test_connection

    engine = get_db_engine(test_settings)
    connection = engine.connect()
    transaction = connection.begin()

    # Configure the test connection for transactional isolation
    set_test_connection(connection)

    # Create session bound to this connection
    session = Session(bind=connection)

    # Configure factories to use this session
    set_factory_session(session)

    # Create API with session pointing to this connection
    api = create_api(settings=test_settings)
    api.dependency_overrides[get_sqlalchemy_session] = get_transactional_session
    api.dependency_overrides[get_settings] = get_test_runner_settings

    if login:
        email = 'testloginadmin@testadmin.com' if admin else 'testloginregular@testuser.com'
        user = get_test_user(email)
        api.dependency_overrides[auth.get_current_user] = lambda: user
        api.dependency_overrides[auth.get_current_user_or_none] = lambda: user
        if admin:
            api.dependency_overrides[auth.get_admin_user] = lambda: user
        logger.info(f'Transactional API: Logged in {"admin" if admin else "regular"} user: {user.email}')

    client = TestClient(api)

    yield client, session

    # Cleanup: rollback transaction (undoes all changes)
    clear_factory_session()
    session.close()
    clear_test_connection()
    transaction.rollback()

    # Reset sequences since rollback doesn't affect sequences
    reset_sequences(engine)

    connection.close()


@pytest.fixture(scope='function')
def txn_api(create_drop_tables):
    """Create transactional API client without authentication.

    All operations are rolled back after the test - no cleanup needed.

    Usage:
        def test_something(txn_api):
            client, session = txn_api
            # Insert data directly or use factories
            session.add(models.Article(title='Test'))
            session.flush()  # Make data visible to API calls
            response = client.get('/articles/')
    """
    with create_transactional_api_client() as (client, session):
        yield client, session


@pytest.fixture(scope='function')
def txn_api_logged_in(create_drop_tables):
    """Create transactional API client with logged-in regular user.

    All operations are rolled back after the test - no cleanup needed.

    Usage:
        def test_something(txn_api_logged_in):
            client, session = txn_api_logged_in
            from tests.factories import TaskFactory
            TaskFactory(name='Test Task')  # Uses transactional session
            response = client.get('/tasks/')
    """
    with create_transactional_api_client(login=True) as (client, session):
        yield client, session


@pytest.fixture(scope='function')
def txn_api_logged_in_admin(create_drop_tables):
    """Create transactional API client with logged-in admin user.

    All operations are rolled back after the test - no cleanup needed.
    """
    with create_transactional_api_client(login=True, admin=True) as (client, session):
        yield client, session
