"""Test factories for generating database objects.

Factories create test data with predictable, explicit defaults.
They support both:
1. Behavior testing - Create specific data to verify business logic
2. Edge case testing - Easily create unusual scenarios

Quick Start:
    def test_search_finds_matching_tasks(factory_session, test_api_logged_in):
        from tests.factories import TaskFactory
        from ichrisbirch.models.task import TaskCategory

        # Create specific data for this test
        TaskFactory(name='Home cleaning', category=TaskCategory.Home)
        TaskFactory(name='Home repairs', category=TaskCategory.Home)
        TaskFactory(name='Work project', category=TaskCategory.Work)

        # Test behavior
        response = test_api_logged_in.get('/tasks/search/', params={'q': 'home'})
        assert len(response.json()) == 2  # Exactly 2 home tasks

Session Management:
    Factories require a SQLAlchemy session. Use the factory_session fixture
    defined in conftest.py.
"""

from .articles import ArticleFactory
from .autotasks import AutoTaskFactory
from .base import clear_factory_session
from .base import get_factory_session
from .base import set_factory_session
from .books import BookFactory
from .boxes import BoxFactory
from .boxes import BoxItemFactory
from .chats import ChatFactory
from .chats import ChatMessageFactory
from .countdowns import CountdownFactory
from .events import EventFactory
from .habits import HabitCategoryFactory
from .habits import HabitCompletedFactory
from .habits import HabitFactory
from .money_wasted import MoneyWastedFactory
from .tasks import TaskFactory
from .users import UserFactory

__all__ = [
    # Core models
    'TaskFactory',
    'UserFactory',
    # Habits
    'HabitFactory',
    'HabitCategoryFactory',
    'HabitCompletedFactory',
    # Other models
    'ArticleFactory',
    'AutoTaskFactory',
    'BookFactory',
    'BoxFactory',
    'BoxItemFactory',
    'ChatFactory',
    'ChatMessageFactory',
    'CountdownFactory',
    'EventFactory',
    'MoneyWastedFactory',
    # Session management
    'set_factory_session',
    'clear_factory_session',
    'get_factory_session',
]
