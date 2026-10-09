"""`admin.signup_settings` created and seeded by its migration, run through alembic."""

import pytest
import sqlalchemy as sa
from alembic import command
from sqlalchemy.exc import IntegrityError

from ichrisbirch.database.initialization import alembic_config
from ichrisbirch.database.session import get_db_engine
from tests.utils.database import test_settings

BEFORE_SIGNUP_SETTINGS = 'e0f1a2b3c4d5'


@pytest.fixture
def engine():
    engine = get_db_engine(test_settings)
    yield engine
    command.upgrade(alembic_config(test_settings), 'head')


def test_the_migration_seeds_signups_closed(engine):
    command.downgrade(alembic_config(test_settings), BEFORE_SIGNUP_SETTINGS)
    assert not sa.inspect(engine).has_table('signup_settings', schema='admin')

    command.upgrade(alembic_config(test_settings), 'head')

    with engine.connect() as conn:
        rows = conn.execute(sa.text('SELECT id, is_open FROM admin.signup_settings')).all()
    assert [tuple(row) for row in rows] == [(1, False)]


def test_a_second_row_is_refused(engine):
    with pytest.raises(IntegrityError, match='single_row'), engine.begin() as conn:
        conn.execute(sa.text('INSERT INTO admin.signup_settings (id, is_open) VALUES (2, true)'))
