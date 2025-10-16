from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from ichrisbirch.config import Settings
from ichrisbirch.config import settings


# @functools.cache
def get_db_engine(settings: Settings) -> Engine:
    return create_engine(
        settings.sqlalchemy.db_uri,
        echo=settings.sqlalchemy.echo,
        pool_pre_ping=True,
        pool_recycle=5,
        connect_args={
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5,
        },
    )


@contextmanager
def create_session(settings: Settings = settings):
    """Get the SQLAlchemy session factory configured for the application."""
    Session = sessionmaker(bind=get_db_engine(settings), autoflush=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def get_sqlalchemy_session() -> Generator[Session, None, None]:
    """Return `sqlalchemy.orm.Session` with automatic cleanup.

    Use this for FastAPI dependency injection:

    >>> @router.get('/{id}/')
    >>> async def read_habit(id: int, session: Session = Depends(get_sqlalchemy_session)):
    >>>     return session.get(models.Habit, id)
    """
    with create_session() as session:
        yield session
