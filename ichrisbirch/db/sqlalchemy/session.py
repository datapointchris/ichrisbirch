from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ichrisbirch.config import settings

engine = create_engine(settings.sqlalchemy.SQLALCHEMY_DATABASE_URI, echo=True)
# connect_args={'check_same_thread': False}
SessionLocal = sessionmaker(bind=engine, autoflush=False)


def sqlalchemy_session() -> Generator:
    """Yields sqlalchemy Session"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
