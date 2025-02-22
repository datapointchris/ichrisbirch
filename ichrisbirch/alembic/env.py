from logging.config import fileConfig

from alembic import context

# from sqlalchemy import engine_from_config
from sqlalchemy import pool

from ichrisbirch.config import settings
from ichrisbirch.database.sqlalchemy.base import Base
from ichrisbirch.database.sqlalchemy.session import engine

# Need the models imported for Base to find the tables
from ichrisbirch.models import Apartment  # noqa
from ichrisbirch.models import Article  # noqa
from ichrisbirch.models import AutoTask  # noqa
from ichrisbirch.models import Box  # noqa
from ichrisbirch.models import BoxItem  # noqa
from ichrisbirch.models import Countdown  # noqa
from ichrisbirch.models import Event  # noqa
from ichrisbirch.models import Habit  # noqa
from ichrisbirch.models import HabitCategory
from ichrisbirch.models import HabitCompleted
from ichrisbirch.models import JournalEntry  # noqa
from ichrisbirch.models import PortfolioProject  # noqa
from ichrisbirch.models import Task  # noqa
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

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine, though an Engine is acceptable here as well.  By
    skipping the Engine creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the script output.
    """
    url = settings.sqlalchemy.db_uri
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection with the context.
    """
    # connectable = engine
    # connectable = engine_from_config(
    #     alembic_config.get_section(alembic_config.config_ini_section),
    #     prefix="sqlalchemy.",
    #     poolclass=pool.NullPool,
    # )

    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
