"""The schema the migrations build is the schema the models declare.

This runs `alembic check` through `env.py` against the session's database,
which pytest has migrated to head. It raises with the proposed operations when
the two differ.
"""

from alembic import command

from ichrisbirch.database.initialization import alembic_config
from tests.utils.database import test_settings


def test_alembic_check_proposes_no_operations():
    command.check(alembic_config(test_settings))
