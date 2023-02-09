import logging

import sqlalchemy
from db.sqlalchemy.session import SessionLocal, engine
from sqlalchemy.schema import CreateSchema

from ichrisbirch import settings

logger = logging.getLogger(__name__)
inspector = sqlalchemy.inspect(engine)

with SessionLocal() as session:
    for schema_name in settings.DB_SCHEMAS:
        if schema_name not in inspector.get_schema_names():
            session.execute(CreateSchema(schema_name))
            logger.info(f'Created schema: {schema_name}')
    session.commit()
