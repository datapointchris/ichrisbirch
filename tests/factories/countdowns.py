"""Countdown factory for generating test Countdown objects."""

from datetime import date
from datetime import timedelta

import factory

from ichrisbirch.models.countdown import Countdown

from .base import get_factory_session


class CountdownFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Countdown objects."""

    class Meta:
        model = Countdown
        sqlalchemy_session_factory = get_factory_session
        sqlalchemy_session_persistence = 'commit'

    name = factory.Sequence(lambda n: f'Test Countdown {n + 1}')
    notes = factory.LazyAttribute(lambda obj: f'Notes for {obj.name}')
    due_date = factory.LazyFunction(lambda: date.today() + timedelta(days=30))

    class Params:
        # Usage: CountdownFactory(past_due=True)
        past_due = factory.Trait(due_date=factory.LazyFunction(lambda: date.today() - timedelta(days=1)))
        # Usage: CountdownFactory(due_today=True)
        due_today = factory.Trait(due_date=factory.LazyFunction(date.today))
