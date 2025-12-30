"""Habit factories for generating test Habit, HabitCategory, and HabitCompleted objects.

By default, creating a Habit will also create its associated category.

Examples:
    # Create habit with auto-generated category
    habit = HabitFactory()

    # Create habit with existing category
    category = HabitCategoryFactory(name='Exercise')
    habit = HabitFactory(category=category)

    # Create current vs hibernated habits
    current = HabitFactory(is_current=True)
    hibernated = HabitFactory(hibernated=True)

    # Create completed habit record
    completed = HabitCompletedFactory()
"""

from datetime import datetime

import factory

from ichrisbirch.models.habit import Habit
from ichrisbirch.models.habitcategory import HabitCategory
from ichrisbirch.models.habitcompleted import HabitCompleted

from .base import get_factory_session


class HabitCategoryFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating HabitCategory objects."""

    class Meta:
        model = HabitCategory
        sqlalchemy_session_factory = get_factory_session
        sqlalchemy_session_persistence = 'commit'

    name = factory.Sequence(lambda n: f'Test Category {n + 1}')
    is_current = True

    class Params:
        hibernated = factory.Trait(is_current=False)


class HabitFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Habit objects.

    Creates an associated HabitCategory by default.
    """

    class Meta:
        model = Habit
        sqlalchemy_session_factory = get_factory_session
        sqlalchemy_session_persistence = 'commit'

    name = factory.Sequence(lambda n: f'Test Habit {n + 1}')
    is_current = True

    # SubFactory creates a category automatically
    category = factory.SubFactory(HabitCategoryFactory)
    category_id = factory.LazyAttribute(lambda obj: obj.category.id if obj.category else None)

    class Params:
        hibernated = factory.Trait(is_current=False)
        with_hibernated_category = factory.Trait(category=factory.SubFactory(HabitCategoryFactory, is_current=False))

    @classmethod
    def with_category(cls, category: HabitCategory, **kwargs):
        """Create a habit with a specific existing category."""
        return cls(category=category, **kwargs)


class HabitCompletedFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating HabitCompleted objects.

    Records a completed habit occurrence.
    """

    class Meta:
        model = HabitCompleted
        sqlalchemy_session_factory = get_factory_session
        sqlalchemy_session_persistence = 'commit'

    name = factory.Sequence(lambda n: f'Completed Habit {n + 1}')
    complete_date = factory.LazyFunction(datetime.now)

    # SubFactory creates a category automatically
    category = factory.SubFactory(HabitCategoryFactory)
    category_id = factory.LazyAttribute(lambda obj: obj.category.id if obj.category else None)

    @classmethod
    def with_category(cls, category: HabitCategory, **kwargs):
        """Create a completed habit record with a specific category."""
        return cls(category=category, **kwargs)
