# Base needs the models imported before being used by Alembic
from sqlalchemy.orm import declarative_base


Base = declarative_base()
