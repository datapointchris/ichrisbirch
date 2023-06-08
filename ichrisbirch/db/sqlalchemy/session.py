from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


from ichrisbirch.config import get_settings

settings = get_settings()
engine = create_engine(settings.sqlalchemy.db_uri, echo=settings.sqlalchemy.echo)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


def sqlalchemy_session() -> Generator[Session, None, None]:
    """Yields sqlalchemy Session"""
    with SessionLocal() as session:
        yield session
