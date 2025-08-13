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

import logging

import sqlalchemy
from sqlalchemy import exc as sqlalchemy_exc
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateSchema

from ichrisbirch.database.sqlalchemy.base import Base
from ichrisbirch.database.sqlalchemy.session import create_session
from ichrisbirch.database.sqlalchemy.session import get_db_engine
from ichrisbirch.models import User

logger = logging.getLogger(__name__)


def create_schemas(session: Session, settings) -> None:
    """Create database schemas if they don't exist."""
    inspector = sqlalchemy.inspect(get_db_engine(settings))
    existing_schemas = inspector.get_schema_names()

    for schema_name in settings.postgres.db_schemas:
        if schema_name not in existing_schemas:
            session.execute(CreateSchema(schema_name))
            logger.info(f'Created schema: {schema_name}')
        else:
            logger.info(f'Schema {schema_name} already exists')

    session.commit()


def create_tables(settings, use_alembic: bool = True) -> None:
    """Create database tables."""
    if use_alembic:
        logger.info('Table creation should be handled by Alembic migrations')
        logger.info('Run: alembic upgrade head')
        return

    logger.info('Creating tables using Base.metadata.create_all()')
    engine = get_db_engine(settings)
    Base.metadata.create_all(engine)
    logger.info('Successfully created all tables')


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
                logger.info(f'User {user.email} already exists')
                continue

            session.add(user)
            session.commit()
            logger.info(f'Created user: {user.name} ({user.email})')
        except sqlalchemy_exc.IntegrityError:
            logger.info(f'User {user.email} already exists (integrity error)')
            session.rollback()


def full_initialization(settings, use_alembic: bool = True) -> None:
    """Perform complete database initialization."""
    logger.info(f'Starting database initialization for environment: {settings.ENVIRONMENT}')

    with create_session(settings) as session:
        create_schemas(session, settings)
        insert_default_users(session, settings)

    create_tables(settings, use_alembic=use_alembic)
    logger.info('Database initialization completed successfully!')


def main():
    """Command line interface for database initialization."""
    import argparse
    import os

    from ichrisbirch.config import get_settings

    parser = argparse.ArgumentParser(description='Initialize database with schemas and default users')
    parser.add_argument(
        '--env',
        type=str,
        choices=['development', 'testing', 'production'],
        help='Environment to initialize (affects which SSM parameters are loaded)',
    )
    parser.add_argument(
        '--use-metadata', action='store_true', help='Use Base.metadata.create_all() instead of Alembic migrations to create tables'
    )

    args = parser.parse_args()

    if args.env:
        os.environ['ENVIRONMENT'] = args.env
        logger.info(f'Environment set to: {args.env}')

    try:
        settings = get_settings()
        logger.info(f'Loaded settings for environment: {getattr(settings, "ENVIRONMENT", "unknown")}')

        full_initialization(settings, use_alembic=not args.use_metadata)

    except Exception as e:
        logger.error(f'Database initialization failed: {e}')
        raise


if __name__ == '__main__':
    import logging

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main()
