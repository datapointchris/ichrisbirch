"""AutoTask factory for generating test AutoTask objects."""

from datetime import datetime
from datetime import timedelta

import factory

from ichrisbirch.models.autotask import AutoTask
from ichrisbirch.models.autotask import AutoTaskFrequency
from ichrisbirch.models.task import TaskCategory

from .base import get_factory_session


class AutoTaskFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating AutoTask objects."""

    class Meta:
        model = AutoTask
        sqlalchemy_session_factory = get_factory_session
        sqlalchemy_session_persistence = 'flush'

    name = factory.Sequence(lambda n: f'Test AutoTask {n + 1}')
    notes = factory.LazyAttribute(lambda obj: f'Notes for {obj.name}')
    category = TaskCategory.Chore
    priority = factory.Sequence(lambda n: (n + 1) * 5)
    max_concurrent = 2
    frequency = AutoTaskFrequency.Weekly
    first_run_date = factory.LazyFunction(datetime.now)
    last_run_date = factory.LazyFunction(datetime.now)
    run_count = 0

    class Params:
        # Usage: AutoTaskFactory(daily=True)
        daily = factory.Trait(frequency=AutoTaskFrequency.Daily)
        # Usage: AutoTaskFactory(monthly=True)
        monthly = factory.Trait(frequency=AutoTaskFrequency.Monthly)
        # Usage: AutoTaskFactory(should_run=True) - last run was long ago
        should_run = factory.Trait(last_run_date=factory.LazyFunction(lambda: datetime.now() - timedelta(days=30)))
        # Usage: AutoTaskFactory(ran_today=True)
        ran_today = factory.Trait(last_run_date=factory.LazyFunction(datetime.now), run_count=1)
