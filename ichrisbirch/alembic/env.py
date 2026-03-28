from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool

from ichrisbirch.config import get_settings
from ichrisbirch.database.base import Base

# Need the models imported for Base to find the tables
from ichrisbirch.models import Article  # noqa
from ichrisbirch.models import ArticleFailedImport  # noqa
from ichrisbirch.models import AutoTask  # noqa
from ichrisbirch.models import AutoTaskFrequency  # noqa
from ichrisbirch.models import BackupHistory  # noqa
from ichrisbirch.models import BackupRestore  # noqa
from ichrisbirch.models import Book  # noqa
from ichrisbirch.models import BookOwnership  # noqa
from ichrisbirch.models import BookProgress  # noqa
from ichrisbirch.models import Box  # noqa
from ichrisbirch.models import BoxItem  # noqa
from ichrisbirch.models import BoxSize  # noqa
from ichrisbirch.models import Chat  # noqa
from ichrisbirch.models import ChatMessage  # noqa
from ichrisbirch.models import Countdown  # noqa
from ichrisbirch.models import Duration  # noqa
from ichrisbirch.models import DurationNote  # noqa
from ichrisbirch.models import Event  # noqa
from ichrisbirch.models import Habit  # noqa
from ichrisbirch.models import HabitCategory  # noqa
from ichrisbirch.models import HabitCompleted  # noqa
from ichrisbirch.models import JWTRefreshToken  # noqa
from ichrisbirch.models import MoneyWasted  # noqa
from ichrisbirch.models import PersonalAPIKey  # noqa
from ichrisbirch.models import Project  # noqa
from ichrisbirch.models import ProjectItem  # noqa
from ichrisbirch.models import ProjectItemDependency  # noqa
from ichrisbirch.models import ProjectItemMembership  # noqa
from ichrisbirch.models import SchedulerJobRun  # noqa
from ichrisbirch.models import Task  # noqa
from ichrisbirch.models import TaskCategory  # noqa
from ichrisbirch.models import User  # noqa

# settings from ichrisbirch/config.py


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
alembic_config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)

# for 'autogenerate' support
target_metadata = Base.metadata

# Tables managed by external libraries (not our models) that autogenerate should ignore
EXCLUDED_TABLES = {'apscheduler_jobs'}


def include_name(name, type_, parent_names):
    if type_ == 'table' and name in EXCLUDED_TABLES:
        return False
    return True

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def _get_db_url():
    """Get the database URL, preferring the config option over settings.

    When called programmatically (e.g., from run_alembic_migrations), the URL
    is set on the config object. When called via the alembic CLI, it falls
    back to get_settings().
    """
    url = alembic_config.get_main_option('sqlalchemy.url')
    if url:
        return url
    settings = get_settings()
    return settings.sqlalchemy.db_uri


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine, though an Engine is acceptable here as well.  By
    skipping the Engine creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the script output.
    """
    url = _get_db_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_name=include_name,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection with the context.
    """
    from sqlalchemy import create_engine

    url = _get_db_url()
    connectable = create_engine(url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_name=include_name,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
