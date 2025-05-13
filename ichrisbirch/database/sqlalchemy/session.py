import functools
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from ichrisbirch.config import Settings
from ichrisbirch.config import get_settings


# Use lazy loading for settings and engine to ensure environment variables are properly set
@functools.lru_cache(2)
def get_db_engine(settings: Settings = get_settings()) -> Engine:
    return create_engine(
        settings.sqlalchemy.db_uri,
        echo=settings.sqlalchemy.echo,
        pool_pre_ping=True,
        pool_recycle=5,
        connect_args={
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        },
    )


def get_session_factory(engine: Engine = get_db_engine()) -> sessionmaker:
    return sessionmaker(bind=engine, autoflush=False)


SessionLocal: sessionmaker[Session] = get_session_factory()


def get_sqlalchemy_session() -> Generator[Session, None, None]:
    """Return `sqlalchemy.orm.Session`

    The difference between return and yield in this context is related to how they
    handle the execution flow and the type of object they produce.

    `return SessionLocal()`:
    This will create a new SQLAlchemy `Session` instance and return it immediately.
    The function execution ends there, and you get a Session object.
    You can use this session to interact with your database, but you'll need to manually close it when you're done.

    `yield SessionLocal()`:
    This will also create a new SQLAlchemy Session instance, but instead of returning it immediately, it yields it.
    This means the function execution is paused, and control is returned to the caller along with the yielded session.
    The function becomes a generator function, and you can resume its execution later.
    This is useful when you want to ensure cleanup code runs after the session is used, like closing the session.
    However, a generator object doesn't have the `__enter__` and `__exit__` methods required for a `with` statement.

    In this case, if you want to use the session with a `with` statement for automatic resource management,
    you should use `return SessionLocal()`.
    If you want to ensure some cleanup code runs after the session is used,
    you can use `yield SessionLocal()`,
    but you'll need to manually close the session in the caller code
    or use contextlib.closing to make the generator usable with a with statement.
    """
    with SessionLocal() as session:
        yield session


# Alias for compatibility with existing code
get_db = get_sqlalchemy_session
