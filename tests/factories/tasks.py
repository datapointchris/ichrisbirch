"""Task factory for generating test Task objects.

Examples:
    # Basic creation with predictable defaults
    task = TaskFactory()

    # Override fields for specific test scenarios
    task = TaskFactory(name='Searchable Home Task', category='Home')

    # Create completed task for testing filters
    completed = TaskFactory(completed=True)

    # Batch creation for testing counts
    TaskFactory.create_batch(5)

    # Test edge cases
    TaskFactory(pinned=True)
    TaskFactory(notes='x' * 10000)
"""

import datetime as dt

import factory

from ichrisbirch.models.task import Task

from .base import get_factory_session


class TaskFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Task objects with predictable defaults."""

    class Meta:
        model = Task
        sqlalchemy_session_factory = get_factory_session
        sqlalchemy_session_persistence = 'flush'

    # Predictable defaults - Sequence ensures unique names
    name = factory.Sequence(lambda n: f'Test Task {n + 1}')
    notes = factory.LazyAttribute(lambda obj: f'Notes for {obj.name}')
    category = 'Chore'
    window_days = 30
    add_date = factory.LazyFunction(lambda: dt.datetime.now(dt.UTC))
    # Each task ranks a day after the one before, so creation order is queue order.
    rank_at = factory.Sequence(lambda n: dt.datetime.now(dt.UTC) + dt.timedelta(days=n + 1))
    pinned = False
    complete_date = None

    class Params:
        # Usage: TaskFactory(completed=True)
        completed = factory.Trait(complete_date=factory.LazyFunction(lambda: dt.datetime.now(dt.UTC)))
        dropped = factory.Trait(drop_date=factory.LazyFunction(lambda: dt.datetime.now(dt.UTC)))

    @classmethod
    def completed_task(cls, **kwargs):
        """Create a completed task."""
        return cls(completed=True, **kwargs)

    @classmethod
    def searchable(cls, search_term: str, **kwargs):
        """Create a task that will match a search term."""
        return cls(name=f'{search_term} task', notes=f'Contains {search_term} in notes', **kwargs)
