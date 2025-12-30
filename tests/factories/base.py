"""Base factory configuration for test factories.

Factory_boy requires a SQLAlchemy session to create and commit objects.
This module provides simple session management for test factories.

Usage:
    # In conftest.py fixture:
    @pytest.fixture
    def factory_session():
        with create_session(test_settings) as session:
            set_factory_session(session)
            yield session
            clear_factory_session()

    # In tests:
    def test_something(factory_session):
        task = TaskFactory(name='My Task')  # Created in factory_session
"""

from sqlalchemy.orm import Session

# Module-level session holder - factories read from this
_factory_session: Session | None = None


def set_factory_session(session: Session) -> None:
    """Set the SQLAlchemy session for all factories."""
    global _factory_session
    _factory_session = session


def clear_factory_session() -> None:
    """Clear the factory session after tests complete."""
    global _factory_session
    _factory_session = None


def get_factory_session() -> Session:
    """Get the current factory session.

    Called by factories to get their session.
    """
    if _factory_session is None:
        raise RuntimeError('Factory session not configured. Use the factory_session fixture or call set_factory_session() first.')
    return _factory_session
