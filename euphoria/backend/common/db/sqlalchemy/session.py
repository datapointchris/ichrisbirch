from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from ...config import get_config_for_environment

config = get_config_for_environment()

engine = create_engine(
    config.SQLALCHEMY_DATABASE_URI, echo=False, future=True
)  # connect_args={'check_same_thread': False}


SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


async def sqlalchemy_session() -> Session:
    """Yields sqlalchemy Session"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
