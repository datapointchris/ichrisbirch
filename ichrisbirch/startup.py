import logging

import sqlalchemy
from sqlalchemy.schema import CreateSchema

from ichrisbirch.config import get_settings
from ichrisbirch.database.sqlalchemy.session import SessionLocal
from ichrisbirch.database.sqlalchemy.session import engine

settings = get_settings()
logger = logging.getLogger('ichrisbirch')
inspector = sqlalchemy.inspect(engine)

# TODO: [2023/05/02] - Write this
# Help me write a startup script for this entire project

with SessionLocal() as session:
    for schema_name in settings.DB_SCHEMAS:
        if schema_name not in inspector.get_schema_names():
            session.execute(CreateSchema(schema_name))
            logger.info(f'Created schema: {schema_name}')
