from sqlite3 import ProgrammingError
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base

engine = create_engine('postgresql:///euphoria', echo=False, future=True)
session = Session(engine, future=True)

# TODO: This can be removed when moving to Alembic to create the schemas and tables
# schemas = ['apartments', 'box_packing', 'countdowns', 'events', 'habits', 'journal', 'portfolio', 'tasks']
# with session:
#     for schema_name in schemas:
#         session.execute(f'CREATE SCHEMA IF NOT EXISTS {schema_name};')


Base = declarative_base()
# Base.metadata.create_all(bind=engine)
