import logging

import sqlalchemy
from sqlalchemy.schema import CreateSchema

from ichrisbirch.config import get_settings
from ichrisbirch.database.sqlalchemy.session import engine, sqlalchemy_session

settings = get_settings()
logger = logging.getLogger(__name__)
inspector = sqlalchemy.inspect(engine)

# TODO: [2023/05/02] - Write this
# Help me write a startup script for this entire project
session = next(sqlalchemy_session())

for schema_name in settings.db_schemas:
    if schema_name not in inspector.get_schema_names():
        session.execute(CreateSchema(schema_name))
        logger.info(f'Created schema: {schema_name}')
