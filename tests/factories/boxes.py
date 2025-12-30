"""Box and BoxItem factories for generating test objects."""

import factory

from ichrisbirch.models.box import Box
from ichrisbirch.models.box import BoxSize
from ichrisbirch.models.boxitem import BoxItem

from .base import get_factory_session


class BoxFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Box objects."""

    class Meta:
        model = Box
        sqlalchemy_session_factory = get_factory_session
        sqlalchemy_session_persistence = 'flush'

    number = factory.Sequence(lambda n: n + 1)
    name = factory.Sequence(lambda n: f'Test Box {n + 1}')
    size = BoxSize.Medium
    essential = False
    warm = False
    liquid = False

    class Params:
        # Usage: BoxFactory(essential_box=True)
        essential_box = factory.Trait(essential=True)
        # Usage: BoxFactory(small=True)
        small = factory.Trait(size=BoxSize.Small)
        # Usage: BoxFactory(large=True)
        large = factory.Trait(size=BoxSize.Large)


class BoxItemFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating BoxItem objects.

    By default creates an associated Box. To create an orphan item,
    pass box=None.
    """

    class Meta:
        model = BoxItem
        sqlalchemy_session_factory = get_factory_session
        sqlalchemy_session_persistence = 'flush'

    name = factory.Sequence(lambda n: f'Test Item {n + 1}')
    essential = False
    warm = False
    liquid = False

    # SubFactory creates a box automatically
    box = factory.SubFactory(BoxFactory)
    box_id = factory.LazyAttribute(lambda obj: obj.box.id if obj.box else None)

    class Params:
        # Usage: BoxItemFactory(orphan=True) - item without a box
        orphan = factory.Trait(box=None, box_id=None)
        # Usage: BoxItemFactory(essential_item=True)
        essential_item = factory.Trait(essential=True)
        # Usage: BoxItemFactory(liquid_item=True)
        liquid_item = factory.Trait(liquid=True)

    @classmethod
    def in_box(cls, box: Box, **kwargs):
        """Create an item in a specific box."""
        return cls(box=box, **kwargs)
