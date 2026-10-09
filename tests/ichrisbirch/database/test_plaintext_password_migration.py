"""Stored plaintext user passwords hashed by migration, run through alembic."""

import logging

import pytest
import sqlalchemy as sa
from alembic import command
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from ichrisbirch.database.initialization import alembic_config
from ichrisbirch.database.session import get_db_engine
from tests.utils.database import test_settings

BEFORE_HASHING = 'c8d9e0f1a2b3'
PLAINTEXT = {'email': 'plaintext-probe@test.com', 'alternative_id': 9_000_000_000_000_000_001}
HASHED = {'email': 'hashed-probe@test.com', 'alternative_id': 9_000_000_000_000_000_002}
PLAINTEXT_PASSWORD = 'a-password-patched-before-the-fix'


@pytest.fixture
def engine():
    engine = get_db_engine(test_settings)
    yield engine
    command.upgrade(alembic_config(test_settings), 'head')
    with engine.begin() as conn:
        conn.execute(
            sa.text('DELETE FROM users WHERE email IN (:plaintext, :hashed)'), {'plaintext': PLAINTEXT['email'], 'hashed': HASHED['email']}
        )


def insert_user(conn, user: dict, password: str) -> None:
    statement = sa.text(
        'INSERT INTO users (alternative_id, name, email, password, is_admin, created_on, last_login, preferences) '
        "VALUES (:alternative_id, :email, :email, :password, false, now(), now(), '{}')"
    )
    conn.execute(statement, user | {'password': password})


def stored_password(conn, user: dict) -> str:
    return conn.execute(sa.text('SELECT password FROM users WHERE email = :email'), {'email': user['email']}).scalar_one()


def test_plaintext_is_hashed_and_a_hash_is_left_alone(engine, caplog):
    existing_hash = generate_password_hash('a-password-set-at-insert')
    command.downgrade(alembic_config(test_settings), BEFORE_HASHING)
    with engine.begin() as conn:
        insert_user(conn, PLAINTEXT, PLAINTEXT_PASSWORD)
        insert_user(conn, HASHED, existing_hash)

    with caplog.at_level(logging.INFO, logger='alembic.runtime.migration'):
        command.upgrade(alembic_config(test_settings), 'head')

    with engine.begin() as conn:
        assert check_password_hash(stored_password(conn, PLAINTEXT), PLAINTEXT_PASSWORD)
        assert stored_password(conn, HASHED) == existing_hash
    assert 'Hashed 1 plaintext user passwords' in caplog.messages
    assert not [message for message in caplog.messages if PLAINTEXT['email'] in message or PLAINTEXT_PASSWORD in message]
