"""MoneyWasted factory for generating test MoneyWasted objects."""

from datetime import date
from datetime import timedelta

import factory

from ichrisbirch.models.money_wasted import MoneyWasted

from .base import get_factory_session


class MoneyWastedFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating MoneyWasted objects."""

    class Meta:
        model = MoneyWasted
        sqlalchemy_session_factory = get_factory_session
        sqlalchemy_session_persistence = 'flush'

    item = factory.Sequence(lambda n: f'Wasted Item {n + 1}')
    amount = factory.Sequence(lambda n: (n + 1) * 10.0)  # 10, 20, 30...
    date_purchased = factory.LazyFunction(lambda: date.today() - timedelta(days=60))
    date_wasted = factory.LazyFunction(lambda: date.today() - timedelta(days=7))
    notes = factory.LazyAttribute(lambda obj: f'Notes for {obj.item}')

    class Params:
        # Usage: MoneyWastedFactory(expensive=True)
        expensive = factory.Trait(amount=500.0)
        # Usage: MoneyWastedFactory(recent=True)
        recent = factory.Trait(date_wasted=factory.LazyFunction(date.today))
