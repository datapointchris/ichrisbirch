"""`full_initialization` run again against a database already at head.

Every pytest session and every `icbops` start, restart and rebuild runs it, so
a second run has to leave the database as the first one did. It also runs
alembic inside the calling process, whose logging it must leave alone.
"""

import logging

import sqlalchemy as sa
import structlog

from ichrisbirch.database.initialization import full_initialization
from ichrisbirch.database.initialization import run_alembic_migrations
from ichrisbirch.database.session import get_db_engine
from tests.utils.database import test_settings


def _database_state() -> tuple[list[str], str, int]:
    with get_db_engine(test_settings).connect() as conn:
        schemas = sorted(sa.inspect(conn).get_schema_names())
        revision = conn.execute(sa.text('SELECT version_num FROM alembic_version')).scalar_one()
        users = conn.execute(sa.text('SELECT count(*) FROM users')).scalar_one()
    return schemas, revision, users


def test_a_second_initialization_changes_no_schema_revision_or_user():
    full_initialization(test_settings)
    before = _database_state()

    full_initialization(test_settings)

    assert _database_state() == before


def test_running_migrations_in_process_leaves_existing_loggers_enabled():
    """alembic.ini's fileConfig disables every logger that exists when it runs."""
    probe = logging.getLogger('tests.ichrisbirch.database.initialization_probe')
    handlers = list(logging.root.handlers)

    run_alembic_migrations(test_settings)

    assert probe.disabled is False
    assert logging.root.handlers == handlers


def test_stdlib_records_reach_the_structlog_renderer_without_a_log_file():
    """alembic reports each migration through stdlib logging, not structlog.

    pytest runs on the host with no LOG_FILE, the same as the initializer in CI.
    """
    formatters = [handler.formatter for handler in logging.root.handlers]
    assert any(isinstance(formatter, structlog.stdlib.ProcessorFormatter) for formatter in formatters)
