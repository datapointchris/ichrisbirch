"""Event factory for generating test Event objects."""

from datetime import UTC
from datetime import datetime
from datetime import timedelta

import factory

from ichrisbirch.models.event import Event

from .base import get_factory_session


def now_utc():
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


class EventFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Event objects."""

    class Meta:
        model = Event
        sqlalchemy_session_factory = get_factory_session
        sqlalchemy_session_persistence = 'flush'

    name = factory.Sequence(lambda n: f'Test Event {n + 1}')
    date = factory.LazyFunction(lambda: now_utc() + timedelta(days=14))
    venue = factory.Sequence(lambda n: f'Venue {n + 1}')
    url = factory.Sequence(lambda n: f'https://events.com/event/{n + 1}')
    cost = factory.Sequence(lambda n: (n + 1) * 25.0)  # 25, 50, 75...
    attending = True
    notes = factory.LazyAttribute(lambda obj: f'Notes for {obj.name}')

    class Params:
        # Usage: EventFactory(not_attending=True)
        not_attending = factory.Trait(attending=False)
        # Usage: EventFactory(free=True)
        free = factory.Trait(cost=0.0)
        # Usage: EventFactory(past=True)
        past = factory.Trait(date=factory.LazyFunction(lambda: now_utc() - timedelta(days=7)))
        # Usage: EventFactory(today=True)
        today = factory.Trait(date=factory.LazyFunction(now_utc))
