from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from ...common.config import get_config_for_environment

config = get_config_for_environment()

engine = create_engine(
    config.SQLALCHEMY_DATABASE_URI, echo=False, future=True
)  # connect_args={'check_same_thread': False}

Base = declarative_base()
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


async def sqlalchemy_session() -> SessionLocal:
    """Yields sqlalchemy Session using try, finally to avoid indentation using `with`"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
