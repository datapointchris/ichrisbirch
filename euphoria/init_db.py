import logging
from sqlalchemy.schema import CreateSchema
import sqlalchemy

from backend.common.config import env_config
from backend.common.db.sqlalchemy.session import SessionLocal, engine

logger = logging.getLogger(__name__)
inspector = sqlalchemy.inspect(engine)

with SessionLocal() as session:
    for schema_name in env_config.SCHEMAS:
        if schema_name not in inspector.get_schema_names():
            session.execute(CreateSchema(schema_name))
            logger.info(f'Created schema: {schema_name}')
    session.commit()
