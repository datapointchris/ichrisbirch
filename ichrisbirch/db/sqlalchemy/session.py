from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ichrisbirch.config import settings

engine = create_engine(settings.sqlalchemy.SQLALCHEMY_DATABASE_URI, echo=True, future=True)
# connect_args={'check_same_thread': False}
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def sqlalchemy_session() -> Session:
    """Yields sqlalchemy Session"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
