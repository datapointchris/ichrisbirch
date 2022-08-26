from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from ...config import env_config

engine = create_engine(env_config.SQLALCHEMY_DATABASE_URI, echo=True, future=True)
# connect_args={'check_same_thread': False}
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def sqlalchemy_session() -> Session:
    """Yields sqlalchemy Session"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
