import logging
from sqlalchemy.schema import CreateSchema
import sqlalchemy

from backend.common.config import SETTINGS
from backend.common.db.sqlalchemy.session import SessionLocal, engine

logger = logging.getLogger(__name__)
inspector = sqlalchemy.inspect(engine)

with SessionLocal() as session:
    for schema_name in SETTINGS.DB_SCHEMAS:
        if schema_name not in inspector.get_schema_names():
            session.execute(CreateSchema(schema_name))
            logger.info(f'Created schema: {schema_name}')
    session.commit()
