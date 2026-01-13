"""Database initialization for all environments.

This should only be run when a new blank database is created.
Schemas and default users should transfer over from backups if restoring.

Consolidates logic previously scattered across:
- ichrisbirch.startup (deprecated)
- scripts.init_database
- tests.environment.DockerComposeTestEnvironment

Usage:
    from ichrisbirch.database.initialization import create_schemas, insert_default_users

    with create_session(settings) as session:
        create_schemas(session, settings)
        insert_default_users(session, settings)
"""

import sqlalchemy
import structlog
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateSchema

from ichrisbirch.database.base import Base
from ichrisbirch.database.session import create_session
from ichrisbirch.database.session import get_db_engine
from ichrisbirch.models import User

logger = structlog.get_logger()


def create_schemas(session: Session, settings) -> None:
    """Create database schemas if they don't exist."""
    inspector = sqlalchemy.inspect(get_db_engine(settings))
    existing_schemas = inspector.get_schema_names()

    for schema_name in settings.postgres.db_schemas:
        if schema_name not in existing_schemas:
            session.execute(CreateSchema(schema_name))
            logger.info('schema_created', schema_name=schema_name)
        else:
            logger.info('schema_exists', schema_name=schema_name)

    session.commit()


def create_tables(settings, use_alembic: bool = False) -> None:
    """Create database tables."""
    if use_alembic:
        logger.info('tables_use_alembic', message='Run: alembic upgrade head')
        return

    logger.info('tables_creating')
    engine = get_db_engine(settings)
    Base.metadata.create_all(engine)
    logger.info('tables_created')


def insert_default_users(session: Session, settings) -> None:
    """Insert environment-specific default users if they don't exist."""
    default_regular_user = User(
        name=settings.users.default_regular_user_name,
        email=settings.users.default_regular_user_email,
        password=settings.users.default_regular_user_password,
    )
    default_admin_user = User(
        name=settings.users.default_admin_user_name,
        email=settings.users.default_admin_user_email,
        password=settings.users.default_admin_user_password,
        is_admin=True,
    )

    for user in (default_regular_user, default_admin_user):
        try:
            existing_user = session.query(User).filter(User.email == user.email).first()
            if existing_user:
                logger.info('user_exists', email=user.email)
                continue

            session.add(user)
            session.commit()
            logger.info('user_created', name=user.name, email=user.email)
        except IntegrityError:
            logger.info('user_exists_integrity', email=user.email)
            session.rollback()
        except Exception as e:
            logger.error('user_creation_failed', email=user.email, error_type=type(e).__name__, error=str(e))
            session.rollback()
            raise


def full_initialization(settings, use_alembic: bool = False) -> None:
    """Perform complete database initialization."""
    logger.info('db_init_starting', environment=settings.ENVIRONMENT)

    with create_session(settings) as session:
        create_schemas(session, settings)
        create_tables(settings, use_alembic=use_alembic)
        insert_default_users(session, settings)

    logger.info('db_init_completed')


def main():
    """Command line interface for database initialization."""
    import argparse
    import os

    parser = argparse.ArgumentParser(description='Initialize database with schemas and default users')
    parser.add_argument(
        '--env',
        type=str,
        choices=['development', 'testing', 'production'],
        help='Environment to initialize (affects which SSM parameters are loaded)',
    )
    parser.add_argument(
        '--use-alembic', action='store_true', help='Use Base.metadata.create_all() instead of Alembic migrations to create tables'
    )

    # Database connection overrides for external execution
    parser.add_argument('--db-host', type=str, help='Database host (overrides POSTGRES_HOST)')
    parser.add_argument('--db-port', type=str, help='Database port (overrides POSTGRES_PORT)')
    parser.add_argument('--db-user', type=str, help='Database username (overrides POSTGRES_USERNAME)')
    parser.add_argument('--db-password', type=str, help='Database password (overrides POSTGRES_PASSWORD)')
    parser.add_argument('--db-name', type=str, help='Database name (overrides POSTGRES_DB)')

    args = parser.parse_args()

    if args.env:
        os.environ['ENVIRONMENT'] = args.env
        logger.info('environment_set', environment=args.env)

    # Override database connection settings if provided - BEFORE importing settings
    if args.db_host:
        os.environ['POSTGRES_HOST'] = args.db_host
        logger.info('db_host_override', host=args.db_host)
    if args.db_port:
        os.environ['POSTGRES_PORT'] = args.db_port
        logger.info('db_port_override', port=args.db_port)
    if args.db_user:
        os.environ['POSTGRES_USERNAME'] = args.db_user
        logger.info('db_user_override', user=args.db_user)
    if args.db_password:
        os.environ['POSTGRES_PASSWORD'] = args.db_password
        logger.info('db_password_override')
    if args.db_name:
        os.environ['POSTGRES_DB'] = args.db_name
        logger.info('db_name_override', name=args.db_name)

    try:
        # Create fresh settings after environment variable overrides
        from ichrisbirch.config import get_settings

        settings = get_settings()
        logger.info('settings_loaded', environment=getattr(settings, 'ENVIRONMENT', 'unknown'))
        logger.info(
            'db_connection',
            user=settings.postgres.username,
            host=settings.postgres.host,
            port=settings.postgres.port,
            database=settings.postgres.database,
        )

        full_initialization(settings, use_alembic=args.use_alembic)

    except Exception as e:
        logger.error('db_init_failed', error=str(e), error_type=type(e).__name__)
        raise


if __name__ == '__main__':
    main()
