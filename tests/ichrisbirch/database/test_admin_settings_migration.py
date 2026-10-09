"""The session's truncate re-seeds `admin.settings` through `insert_admin_settings`.

So only a downgrade and an upgrade reach the seed in migration `e8d57aa23bca`,
which is the one a production database gets.
"""

import pytest
import sqlalchemy as sa
from alembic import command

from ichrisbirch.database.initialization import alembic_config
from ichrisbirch.database.session import get_db_engine
from tests.utils.database import test_settings

BEFORE_ADMIN_SETTINGS = 'e0f1a2b3c4d5'


@pytest.fixture
def engine():
    engine = get_db_engine(test_settings)
    yield engine
    command.upgrade(alembic_config(test_settings), 'head')


def test_the_migration_seeds_signups_closed(engine):
    command.downgrade(alembic_config(test_settings), BEFORE_ADMIN_SETTINGS)
    assert not sa.inspect(engine).has_table('settings', schema='admin')

    command.upgrade(alembic_config(test_settings), 'head')

    with engine.connect() as conn:
        rows = conn.execute(sa.text('SELECT id, is_signup_open FROM admin.settings')).all()
    assert [tuple(row) for row in rows] == [(1, False)]
