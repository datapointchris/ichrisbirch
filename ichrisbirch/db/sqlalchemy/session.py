from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ichrisbirch.config import settings

DB_URI = settings.sqlalchemy.SQLALCHEMY_DATABASE_URI

engine = create_engine(DB_URI, echo=True)
connect_args = {'check_same_thread': False} if DB_URI.startswith('sqlite') else {}
Session = sessionmaker(bind=engine, autoflush=False, connect_args=connect_args)


def sqlalchemy_session() -> Generator:
    """Yields sqlalchemy Session"""
    with Session() as session:
        yield session
