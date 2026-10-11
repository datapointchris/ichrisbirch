"""Pytest configuration and fixtures.

This module provides pytest fixtures for all test modules, centralizing test setup and teardown.
Each session runs against its own Postgres and Redis, started by `tests.environment.PrivateServices`.
"""

import contextlib
import logging
import threading
import time
from contextlib import contextmanager

import pytest
from apscheduler.schedulers.blocking import BlockingScheduler
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch.api import API_PREFIX
from ichrisbirch.api.endpoints import auth
from ichrisbirch.api.main import create_api
from ichrisbirch.config import get_settings
from ichrisbirch.database.initialization import insert_admin_settings
from ichrisbirch.database.initialization import insert_default_users
from ichrisbirch.database.initialization import insert_lookup_table_data
from ichrisbirch.database.initialization import truncate_all_tables
from ichrisbirch.database.session import create_session
from ichrisbirch.database.session import get_db_engine
from ichrisbirch.database.session import get_sqlalchemy_session
from ichrisbirch.scheduler.main import get_jobstore
from tests import test_data
from tests.environment import PrivateServices
from tests.factories import clear_factory_session
from tests.factories import set_factory_session
from tests.utils.database import clear_test_connection
from tests.utils.database import get_test_login_users
from tests.utils.database import get_test_runner_settings
from tests.utils.database import get_test_session
from tests.utils.database import get_test_user
from tests.utils.database import get_transactional_session
from tests.utils.database import set_test_connection
from tests.utils.database import test_settings

logger = logging.getLogger(__name__)
logger.warning('<-- file imported')

# A test names a resource route as the frontend does, below the prefix: `/tasks/` reaches `/api/v1/tasks/`.
API_BASE_URL = f'http://testserver{API_PREFIX}'

# Cached API apps to avoid expensive recreation for every test
cached_api = None
cached_api_regular = None
cached_api_admin = None


def get_cached_api():
    """Get or create a cached FastAPI app instance (unauthenticated)."""
    global cached_api
    if cached_api is None:
        cached_api = create_api(settings=test_settings)
    return cached_api


def get_cached_api_regular():
    """Get or create a cached FastAPI app for regular user."""
    global cached_api_regular
    if cached_api_regular is None:
        cached_api_regular = create_api(settings=test_settings)
    return cached_api_regular


def get_cached_api_admin():
    """Get or create a cached FastAPI app for admin user."""
    global cached_api_admin
    if cached_api_admin is None:
        cached_api_admin = create_api(settings=test_settings)
    return cached_api_admin


def prewarm_caches():
    """Pre-warm API apps and user cache at session start.

    This avoids the first-test latency (~230ms per API creation, ~104ms for user lookups).
    Called from insert_users_for_login after tables and users are ready.
    """
    start = time.perf_counter()

    # Pre-warm API apps (~230ms each, but done once)
    get_cached_api()
    get_cached_api_regular()
    get_cached_api_admin()

    # Pre-warm user cache (~52ms each, but done once)
    get_test_user('testloginregular@testuser.com')
    get_test_user('testloginadmin@testadmin.com')

    elapsed = (time.perf_counter() - start) * 1000
    logger.info(f'Pre-warmed caches in {elapsed:.1f}ms')


@pytest.fixture(scope='session', autouse=True)
def setup_test_environment():
    """Start this session's own Postgres and Redis, and bring the schema to head."""
    logger.warning('')
    logger.warning(f'{"=" * 30}>  STARTING TESTING  <{"=" * 30}')
    logger.warning('')

    with PrivateServices(test_settings) as services:
        yield services

    logger.warning('')
    logger.warning(f'{"=" * 30}>  TESTING FINISHED  <{"=" * 30}')
    logger.warning('')


@pytest.fixture(scope='session')
def truncate_tables(setup_test_environment):
    """Empty every table the migrations seeded, then insert the rows the app cannot run without."""
    truncate_all_tables(test_settings)
    insert_lookup_table_data(test_settings)
    insert_admin_settings(test_settings)
    with create_session(test_settings) as session:
        insert_default_users(session, test_settings)
    logger.info('cleaned all tables (session scope)')


@pytest.fixture(scope='session', autouse=True)
def insert_users_for_login(truncate_tables):
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

    # Pre-warm caches after users are ready (avoids first-test latency)
    prewarm_caches()


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
    client = TestClient(api, base_url=API_BASE_URL)

    api.dependency_overrides[get_sqlalchemy_session] = get_test_session
    api.dependency_overrides[get_settings] = get_test_runner_settings

    if login:
        email = 'testloginadmin@testadmin.com' if admin else 'testloginregular@testuser.com'
        user = get_test_user(email)
        api.dependency_overrides[auth.get_current_user] = lambda: user
        api.dependency_overrides[auth.get_current_user_or_none] = lambda: user
        api.dependency_overrides[auth.get_current_user_or_scoped_client] = lambda: user
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
    with engine.connect() as reset_conn:
        for seq in SEQUENCES_TO_RESET:
            with contextlib.suppress(Exception):
                reset_conn.execute(text(f'ALTER SEQUENCE {seq} RESTART WITH 1'))
        reset_conn.commit()


@pytest.fixture(scope='function')
def factory_session(truncate_tables):
    """Provide a transactional SQLAlchemy session for factory_boy factories.

    Uses transaction isolation: all operations are wrapped in a transaction
    that is rolled back after the test, automatically cleaning up all data.

    Usage:
        def test_with_factories(factory_session):
            from tests.factories import TaskFactory
            task = TaskFactory(name='My Task', window_days=10)
            assert task.id is not None
            # Data is automatically cleaned up after test via rollback
    """
    engine = get_db_engine(test_settings)
    connection = engine.connect()
    transaction = connection.begin()

    # Configure the test connection for transactional isolation
    set_test_connection(connection)

    # Create session bound to this connection
    session = Session(bind=connection, join_transaction_mode='create_savepoint')

    # Configure factories to use this session
    set_factory_session(session)

    yield session

    # Cleanup: rollback transaction (undoes all changes)
    clear_factory_session()
    session.close()
    clear_test_connection()
    transaction.rollback()

    # Note: Sequence resets removed - transactional rollback handles cleanup.
    # Tests don't need IDs to start from 1; only data isolation matters.
    # This saves ~48ms per test (96% of per-test overhead).

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
    engine = get_db_engine(test_settings)
    connection = engine.connect()
    transaction = connection.begin()

    # Configure the test connection for transactional isolation
    set_test_connection(connection)

    # Create session bound to this connection
    session = Session(bind=connection, join_transaction_mode='create_savepoint')

    # Configure factories to use this session
    set_factory_session(session)

    # Use cached API app to avoid expensive recreation
    api = get_cached_api()

    # Store original overrides to restore later
    original_overrides = api.dependency_overrides.copy()

    # Set up dependency overrides for this test
    api.dependency_overrides[get_sqlalchemy_session] = get_transactional_session
    api.dependency_overrides[get_settings] = get_test_runner_settings

    if login:
        email = 'testloginadmin@testadmin.com' if admin else 'testloginregular@testuser.com'
        user = get_test_user(email)
        api.dependency_overrides[auth.get_current_user] = lambda: user
        api.dependency_overrides[auth.get_current_user_or_none] = lambda: user
        api.dependency_overrides[auth.get_current_user_or_scoped_client] = lambda: user
        if admin:
            api.dependency_overrides[auth.get_admin_user] = lambda: user

    client = TestClient(api, base_url=API_BASE_URL)

    yield client, session

    # Cleanup: restore original overrides, rollback transaction
    api.dependency_overrides = original_overrides
    clear_factory_session()
    session.close()
    clear_test_connection()
    transaction.rollback()

    # Note: Sequence resets removed - transactional rollback handles cleanup.
    # Tests don't need IDs to start from 1; only data isolation matters.
    # This saves ~48ms per test (96% of per-test overhead).

    connection.close()


@pytest.fixture(scope='function')
def txn_api(insert_users_for_login):
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
def txn_api_logged_in(insert_users_for_login):
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
def txn_api_logged_in_admin(insert_users_for_login):
    """Create transactional API client with logged-in admin user.

    All operations are rolled back after the test - no cleanup needed.
    """
    with create_transactional_api_client(login=True, admin=True) as (client, session):
        yield client, session


@contextmanager
def create_multi_client_transactional_context():
    """Create multiple API clients sharing the SAME transaction.

    This solves the deadlock issue when tests need both regular and admin clients.
    All clients share one database connection/transaction, so they can see each
    other's data and won't deadlock.

    Yields:
        dict with keys:
            - 'session': The shared SQLAlchemy session
            - 'client': Unauthenticated API client
            - 'client_logged_in': Regular user API client
            - 'client_admin': Admin user API client
    """
    engine = get_db_engine(test_settings)
    connection = engine.connect()
    transaction = connection.begin()

    # Configure the test connection for transactional isolation
    set_test_connection(connection)

    # Create session bound to this connection
    session = Session(bind=connection, join_transaction_mode='create_savepoint')

    # Configure factories to use this session
    set_factory_session(session)

    # Get cached APIs and store original overrides
    api = get_cached_api()
    api_logged_in = get_cached_api_regular()
    api_admin = get_cached_api_admin()

    original_overrides = api.dependency_overrides.copy()
    original_overrides_regular = api_logged_in.dependency_overrides.copy()
    original_overrides_admin = api_admin.dependency_overrides.copy()

    # Set up base API
    api.dependency_overrides[get_sqlalchemy_session] = get_transactional_session
    api.dependency_overrides[get_settings] = get_test_runner_settings

    # Get users for auth overrides (cached)
    regular_user = get_test_user('testloginregular@testuser.com')
    admin_user = get_test_user('testloginadmin@testadmin.com')

    # Create unauthenticated client
    client = TestClient(api, base_url=API_BASE_URL)

    # Set up regular user API
    api_logged_in.dependency_overrides[get_sqlalchemy_session] = get_transactional_session
    api_logged_in.dependency_overrides[get_settings] = get_test_runner_settings
    api_logged_in.dependency_overrides[auth.get_current_user] = lambda: regular_user
    api_logged_in.dependency_overrides[auth.get_current_user_or_none] = lambda: regular_user
    api_logged_in.dependency_overrides[auth.get_current_user_or_scoped_client] = lambda: regular_user
    client_logged_in = TestClient(api_logged_in, base_url=API_BASE_URL)

    # Set up admin user API
    api_admin.dependency_overrides[get_sqlalchemy_session] = get_transactional_session
    api_admin.dependency_overrides[get_settings] = get_test_runner_settings
    api_admin.dependency_overrides[auth.get_current_user] = lambda: admin_user
    api_admin.dependency_overrides[auth.get_current_user_or_none] = lambda: admin_user
    api_admin.dependency_overrides[auth.get_current_user_or_scoped_client] = lambda: admin_user
    api_admin.dependency_overrides[auth.get_admin_user] = lambda: admin_user
    client_admin = TestClient(api_admin, base_url=API_BASE_URL)

    yield {
        'session': session,
        'client': client,
        'client_logged_in': client_logged_in,
        'client_admin': client_admin,
    }

    # Cleanup: restore original overrides, rollback transaction
    api.dependency_overrides = original_overrides
    api_logged_in.dependency_overrides = original_overrides_regular
    api_admin.dependency_overrides = original_overrides_admin
    clear_factory_session()
    session.close()
    clear_test_connection()
    transaction.rollback()

    # Note: Sequence resets removed - transactional rollback handles cleanup.
    # Tests don't need IDs to start from 1; only data isolation matters.
    # This saves ~48ms per test (96% of per-test overhead).

    connection.close()


@pytest.fixture(scope='function')
def txn_multi_client(insert_users_for_login):
    """Provide multiple API clients sharing the same transaction.

    Use this when a test needs both regular and admin clients to avoid deadlocks.

    Usage:
        def test_something(txn_multi_client):
            ctx = txn_multi_client
            # Use ctx['client'] for unauthenticated requests
            # Use ctx['client_logged_in'] for regular user requests
            # Use ctx['client_admin'] for admin user requests
            # Use ctx['session'] for direct database operations
    """
    with create_multi_client_transactional_context() as ctx:
        yield ctx
