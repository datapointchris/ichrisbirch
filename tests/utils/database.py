"""Database utilities for testing.

This module provides functions for database operations during tests.

=============================================================================
TEST USER TYPES AND THEIR PURPOSES
=============================================================================

This module contains two distinct categories of test users that serve different
testing requirements and have different lifecycles:

1. LOGIN USERS (get_test_login_* functions)
-----------------------------------------
Source: get_test_login_users() function in this file
Email addresses:
  - testloginregular@testuser.com
  - testloginadmin@testadmin.com

Purpose: Persistent authentication users for integration tests
- Inserted once at module scope via insert_users_for_login fixture in conftest.py
- Never deleted - excluded from cleanup in delete_test_data()
- Used for authentication in Flask app tests and frontend tests that need actual login
- Available across all test modules without setup/teardown

Usage:
- conftest.py: Flask app test clients with authentication
- fixtures.py: Playwright frontend tests that perform actual login
- Test clients that override authentication dependencies

2. TEST DATA USERS (get_test_data_* functions)
---------------------------------------------
Source: tests/test_data/users.py as BASE_DATA
Email addresses:
  - regular_user_1@gmail.com
  - regular.user.2@hotmail.com
  - admin@admin.com

Purpose: Temporary test data for API endpoint testing
- Inserted/deleted per test module via @pytest.fixture(autouse=True)
- Fresh data for each test module to ensure isolation
- Used for API business logic testing: authorization, CRUD operations, data validation
- Not for authentication - used as data subjects in API tests

Usage:
- test_auth.py and test_users.py: fixtures that wrap these functions
- API endpoint tests that need specific user data for testing business logic
- Tests that verify user-specific authorization and data access patterns

WHY BOTH ARE NEEDED
==================

Different Test Requirements:
- Integration/Frontend Tests need persistent users for actual login flows
  * Flask app route tests that need authenticated sessions
  * Frontend Playwright tests that fill login forms
  * Tests that verify authentication mechanisms work end-to-end

- API Unit Tests need fresh, controlled data for each test run
  * Testing API authorization logic
  * Verifying user data CRUD operations
  * Testing user-specific business rules
  * Ensuring test isolation and repeatability

Different Lifecycles:
- Login users: Created once per test session, never deleted
- Test data users: Created/deleted per test module for isolation

Different Authentication Patterns:
- Login users: Used with actual authentication (dependency overrides, login forms)
- Test data users: Used as fixture data injected directly into tests

=============================================================================
"""

import copy
import logging
from collections.abc import Generator
from contextlib import contextmanager
from copy import deepcopy
from typing import Any
from typing import TypeVar

from pydantic import BaseModel
from sqlalchemy import Connection
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.orm import Session

import tests.test_data
from ichrisbirch import models
from ichrisbirch.config import Settings
from ichrisbirch.config import settings
from ichrisbirch.database.session import create_session
from ichrisbirch.database.session import get_db_engine

ModelType = TypeVar('ModelType', bound=BaseModel)
logger = logging.getLogger(__name__)

# =============================================================================
# TRANSACTION-BASED TEST ISOLATION
# =============================================================================
# These utilities enable per-test transaction isolation. Each test runs in its
# own transaction that is rolled back after the test, ensuring:
# 1. Tests don't pollute each other's data
# 2. No need for explicit cleanup (delete_test_data)
# 3. Tests can run in parallel safely
# =============================================================================

_test_connection: Connection | None = None


def set_test_connection(conn: Connection) -> None:
    """Set the current test connection for transaction isolation."""
    global _test_connection
    _test_connection = conn


def get_test_connection() -> Connection | None:
    """Get the current test connection."""
    return _test_connection


def clear_test_connection() -> None:
    """Clear the current test connection."""
    global _test_connection
    _test_connection = None


def get_transactional_session() -> Generator[Session, None, None]:
    """Return a session bound to the current test connection.

    This session participates in the test's transaction and will be
    rolled back after the test completes.
    """
    if _test_connection is None:
        raise RuntimeError(
            'No test connection configured. Use the db_transaction fixture or ensure transaction isolation is set up before calling this.'
        )
    session = Session(bind=_test_connection)
    try:
        yield session
    finally:
        session.close()


@contextmanager
def transactional_test_context(settings: Settings):
    """Context manager for transaction-isolated tests.

    Usage:
        with transactional_test_context(test_settings) as session:
            # All operations in this block are in a transaction
            # that will be rolled back when the block exits
            TaskFactory()
            result = session.query(Task).all()
    """
    engine = get_db_engine(settings)
    connection = engine.connect()
    transaction = connection.begin()

    set_test_connection(connection)
    session = Session(bind=connection)

    try:
        yield session
    finally:
        session.close()
        clear_test_connection()
        transaction.rollback()
        connection.close()


def get_test_runner_settings() -> Settings:
    test_settings = copy.deepcopy(settings)
    test_settings.ENVIRONMENT = 'testing'
    test_settings.protocol = 'http'
    test_settings.postgres.host = 'localhost'
    test_settings.postgres.username = 'postgres'
    test_settings.postgres.password = 'postgres'
    test_settings.postgres.port = 5434
    test_settings.sqlalchemy.database = 'ichrisbirch'
    test_settings.sqlalchemy.host = 'localhost'
    test_settings.sqlalchemy.username = 'postgres'
    test_settings.sqlalchemy.password = 'postgres'
    test_settings.sqlalchemy.port = 5434
    test_settings.sqlalchemy.database = 'ichrisbirch'
    test_settings.fastapi.host = 'localhost'
    test_settings.fastapi.port = 8001
    test_settings.flask.host = 'localhost'
    test_settings.flask.port = 5001
    test_settings.redis.host = 'localhost'
    test_settings.redis.port = 6380
    test_settings.chat.host = 'localhost'
    test_settings.chat.port = 8507
    return test_settings


test_settings = get_test_runner_settings()


def get_test_session() -> Generator[Session, None, None]:
    """Return a SQLAlchemy session for testing."""
    with create_session(test_settings) as session:
        yield session


def get_test_login_users() -> list[dict]:
    """Return a list of test users for login testing."""
    # NOTE: These have to be dicts, if they are models.User objects, they will be incorrect
    # when called after the first module that uses them because they will change somehow (sqlalchemy bullshit magic)

    # Sacrificial test user is inserted first to be deleted when testing the users endpoint,
    # so as not to delete the login users

    return [
        {
            'name': 'Test User to be Sacrificed for Delete Test',
            'email': 'sacrifice@testgods.com',
            'password': 'repentance',
        },
        {
            'name': 'Test Login Regular User',
            'email': 'testloginregular@testuser.com',
            'password': 'regularpassword',
        },
        {
            'name': 'Test Login Admin User',
            'email': 'testloginadmin@testadmin.com',
            'password': 'adminpassword',
            'is_admin': True,
        },
    ]


def get_test_user(email: str) -> models.User:
    with create_session(test_settings) as session:
        q = select(models.User).where(models.User.email == email)
        try:
            return session.execute(q).scalar_one()
        except Exception as e:
            logger.error(f'Error retrieving test user {email}: {e}')
            raise e


def get_test_data() -> dict[str, dict[str, Any]]:
    """Return mapping of dataset names to their models and data.

    Note: Some child models are inserted via relationships (not directly):
    - boxitems: inserted via Box.items relationship
    - habits: inserted via HabitCategory.habits relationship
    - chatmessages: inserted via Chat.messages relationship
    These have empty data but are kept for delete_test_data sequence resets.
    """
    return {
        'articles': {'model': models.Article, 'data': tests.test_data.articles.BASE_DATA},
        'autotasks': {'model': models.AutoTask, 'data': tests.test_data.autotasks.BASE_DATA},
        'books': {'model': models.Book, 'data': tests.test_data.books.BASE_DATA},
        'boxes': {'model': models.Box, 'data': tests.test_data.boxes.BASE_DATA},
        'boxitems': {'model': models.BoxItem, 'data': []},  # Inserted via Box.items relationship
        'chats': {'model': models.Chat, 'data': tests.test_data.chats.BASE_DATA},
        'chatmessages': {'model': models.ChatMessage, 'data': []},  # Inserted via Chat.messages relationship
        'countdowns': {'model': models.Countdown, 'data': tests.test_data.countdowns.BASE_DATA},
        'events': {'model': models.Event, 'data': tests.test_data.events.BASE_DATA},
        'habitcategories': {'model': models.HabitCategory, 'data': tests.test_data.habitcategories.BASE_DATA},
        'habits': {'model': models.Habit, 'data': []},  # Inserted via HabitCategory.habits relationship
        'habitscompleted': {'model': models.HabitCompleted, 'data': []},  # Inserted via HabitCategory.completed_habits relationship
        'money_wasted': {'model': models.MoneyWasted, 'data': tests.test_data.money_wasted.BASE_DATA},
        'tasks': {'model': models.Task, 'data': tests.test_data.tasks.BASE_DATA},
        'users': {'model': models.User, 'data': tests.test_data.users.BASE_DATA},
    }


def insert_test_data(*datasets):
    test_data = get_test_data()
    selected_datasets = [deepcopy(test_data[key]['data']) for key in datasets]

    with create_session(test_settings) as session:
        for data in selected_datasets:
            session.add_all(data)
        session.commit()
    for d in datasets:
        logger.info(f'inserted testing dataset: {d}')


def insert_test_data_transactional(session: Session, *datasets):
    """Insert test data into a transactional session (no commit).

    Use this with transactional fixtures like txn_api_logged_in:

        def test_something(txn_api_logged_in):
            client, session = txn_api_logged_in
            insert_test_data_transactional(session, 'tasks')
            session.flush()  # Make data visible to API calls
            response = client.get('/tasks/')

    Unlike insert_test_data(), this:
    - Uses the provided session instead of creating a new one
    - Does NOT commit (the test's transaction will be rolled back)
    - Calls flush() to make data visible within the transaction
    """
    test_data = get_test_data()
    selected_datasets = [deepcopy(test_data[key]['data']) for key in datasets]

    for data in selected_datasets:
        session.add_all(data)
    session.flush()  # Make visible within transaction without committing

    for d in datasets:
        logger.info(f'inserted testing dataset (transactional): {d}')


def delete_test_data(*datasets):
    """Delete test data except login users."""
    test_data = get_test_data()

    with create_session(test_settings) as session:
        for table in datasets:
            table_model = test_data[table]['model']

            if table == 'users':
                login_emails = [user['email'] for user in get_test_login_users()]
                dont_delete_login_users = table_model.email.notin_(login_emails)
                all_table_items = session.execute(select(table_model).where(dont_delete_login_users)).scalars().all()
            else:
                all_table_items = session.execute(select(table_model)).scalars().all()

            for item in all_table_items:
                session.delete(item)

            if table_model.__table__.schema is not None:
                table_name = f'{table_model.__table__.schema}.{table_model.__table__.name}'
            else:
                table_name = table_model.__table__.name

            if 'users' not in table:
                session.execute(text(f'ALTER SEQUENCE {table_name}_id_seq RESTART WITH 1'))
                logger.info(f'reset sequence for {table_name}')

        session.commit()

    for d in datasets:
        logger.info(f'deleted testing dataset: {d}')


def make_app_headers_for_user(user):
    """Create app authentication headers for a user."""
    return {
        'X-Application-ID': test_settings.flask.app_id,
        'X-User-ID': user.get_id(),
        'X-Service-Key': test_settings.auth.internal_service_key,
    }


def make_jwt_header(token: str):
    """Create JWT authorization header."""
    return {'Authorization': f'Bearer {token}'}


def make_internal_service_headers():
    """Create internal service authentication headers."""
    return {
        'X-Internal-Service': 'flask-frontend',
        'X-Service-Key': test_settings.auth.internal_service_key,
    }


def make_invalid_internal_service_headers():
    """Create invalid internal service authentication headers."""
    return {
        'X-Internal-Service': 'flask-frontend',
        'X-Service-Key': 'invalid_key',
    }
