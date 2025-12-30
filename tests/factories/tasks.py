"""Task factory for generating test Task objects.

Examples:
    # Basic creation with predictable defaults
    task = TaskFactory()

    # Override fields for specific test scenarios
    task = TaskFactory(name='Searchable Home Task', category=TaskCategory.Home)

    # Create completed task for testing filters
    completed = TaskFactory(completed=True)

    # Batch creation for testing counts
    TaskFactory.create_batch(5)

    # Test edge cases
    TaskFactory(priority=-5)
    TaskFactory(notes='x' * 10000)
"""

from datetime import datetime

import factory

from ichrisbirch.models.task import Task
from ichrisbirch.models.task import TaskCategory

from .base import get_factory_session


class TaskFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Task objects with predictable defaults."""

    class Meta:
        model = Task
        sqlalchemy_session_factory = get_factory_session
        sqlalchemy_session_persistence = 'commit'

    # Predictable defaults - Sequence ensures unique names
    name = factory.Sequence(lambda n: f'Test Task {n + 1}')
    notes = factory.LazyAttribute(lambda obj: f'Notes for {obj.name}')
    category = TaskCategory.Chore
    priority = factory.Sequence(lambda n: (n + 1) * 5)  # 5, 10, 15, 20...
    add_date = factory.LazyFunction(datetime.now)
    complete_date = None

    class Params:
        # Usage: TaskFactory(completed=True)
        completed = factory.Trait(complete_date=factory.LazyFunction(datetime.now))
        high_priority = factory.Trait(priority=100)
        low_priority = factory.Trait(priority=1)
        negative_priority = factory.Trait(priority=-5)

    @classmethod
    def completed_task(cls, **kwargs):
        """Create a completed task."""
        return cls(completed=True, **kwargs)

    @classmethod
    def searchable(cls, search_term: str, **kwargs):
        """Create a task that will match a search term."""
        return cls(name=f'{search_term} task', notes=f'Contains {search_term} in notes', **kwargs)
