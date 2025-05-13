"""Startup of the project.

This should only be run when a new blank database is created.
Schemas and default users should transfer over from backups if restoring.

Note: The user information is different for each environment. Dev has simple passwords.
"""

import logging

import sqlalchemy
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateSchema

from ichrisbirch.config import Settings
from ichrisbirch.config import get_settings
from ichrisbirch.database.sqlalchemy.session import SessionLocal
from ichrisbirch.database.sqlalchemy.session import get_db_engine
from ichrisbirch.models import User

logger = logging.getLogger('startup')


def create_schemas(session: Session, settings: Settings, logger: logging.Logger):
    inspector = sqlalchemy.inspect(get_db_engine())
    for schema_name in settings.db_schemas:
        if schema_name not in inspector.get_schema_names():
            session.execute(CreateSchema(schema_name))
            logger.info(f'created schema: {schema_name}')


def insert_default_users(session: Session, settings: Settings, logger: logging.Logger):
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
    service_account_user = User(
        name=settings.users.service_account_user_name,
        email=settings.users.service_account_user_email,
        password=settings.users.service_account_user_password,
    )

    for user in (default_regular_user, default_admin_user, service_account_user):
        try:
            session.add(user)
            session.commit()
            logger.info(f'created user: {user.name}')
        except sqlalchemy.exc.IntegrityError:
            logger.warning(f'user {user.name} already exists, skipping')
            session.rollback()
        except Exception as e:
            logger.error(f'error creating user: {user.name}')
            logger.error(e)
            session.rollback()


if __name__ == '__main__':
    settings = get_settings()
    with SessionLocal() as session:
        create_schemas(session, settings, logger)

    with SessionLocal() as session:
        insert_default_users(session, settings, logger)
