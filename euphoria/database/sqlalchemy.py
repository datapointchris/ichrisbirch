from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base

engine = create_engine('postgresql:///euphoria', echo=False, future=True)
session = Session(engine, future=True)

Base = declarative_base()
Base.metadata.create_all(bind=engine)
