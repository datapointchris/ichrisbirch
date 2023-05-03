import logging

import sqlalchemy
from db.sqlalchemy.session import engine, sqlalchemy_session
from sqlalchemy.schema import CreateSchema

from ichrisbirch.config import settings

logger = logging.getLogger(__name__)
inspector = sqlalchemy.inspect(engine)

# TODO: [2023/05/02] - Write this
# Help me write a startup script for this entire project

for schema_name in settings.DB_SCHEMAS:
    if schema_name not in inspector.get_schema_names():
        sqlalchemy_session.execute(CreateSchema(schema_name))
        logger.info(f'Created schema: {schema_name}')
