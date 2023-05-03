from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ichrisbirch.config import settings

engine = create_engine(settings.sqlalchemy.db_uri, echo=True)
Session = sessionmaker(bind=engine, autoflush=False)


def sqlalchemy_session() -> Generator:
    """Yields sqlalchemy Session"""
    with Session() as session:
        yield session
