"""User factory for generating test User objects.

Passwords are automatically hashed by SQLAlchemy's before_insert event.

Examples:
    # Basic creation
    user = UserFactory()

    # Create admin user
    admin = UserFactory(admin=True)

    # Create user with specific email for login testing
    user = UserFactory(email='specific@test.com', password='mypassword')

    # Batch creation
    users = UserFactory.create_batch(3)
"""

import factory

from ichrisbirch.models.user import DEFAULT_USER_PREFERENCES
from ichrisbirch.models.user import User

from .base import get_factory_session


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating User objects with predictable defaults."""

    class Meta:
        model = User
        sqlalchemy_session_factory = get_factory_session
        sqlalchemy_session_persistence = 'commit'

    name = factory.Sequence(lambda n: f'Test User {n + 1}')
    email = factory.Sequence(lambda n: f'testuser{n + 1}@test.com')
    password = 'testpassword'  # Will be hashed by SQLAlchemy event
    is_admin = False
    preferences = factory.LazyFunction(DEFAULT_USER_PREFERENCES.copy)

    class Params:
        # Usage: UserFactory(admin=True)
        admin = factory.Trait(
            is_admin=True,
            name=factory.Sequence(lambda n: f'Admin User {n + 1}'),
            email=factory.Sequence(lambda n: f'admin{n + 1}@test.com'),
        )

    @classmethod
    def admin_user(cls, **kwargs):
        """Create an admin user."""
        return cls(admin=True, **kwargs)

    @classmethod
    def with_credentials(cls, email: str, password: str, **kwargs):
        """Create a user with specific login credentials."""
        return cls(email=email, password=password, **kwargs)
