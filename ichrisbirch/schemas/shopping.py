import datetime as dt
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import StringConstraints
from pydantic import model_validator

from ichrisbirch.schemas.not_null import NotNull

# A section or an item answers to its UUID or its name. Names are unique without
# regard to case, so a name is as good a handle as a number would be.
ShoppingSectionRef = UUID | str
ShoppingItemRef = UUID | str

ShoppingName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

# Which items a read returns: on the list, off it, or the whole catalog.
SHOPPING_ITEM_STATUSES = ('needed', 'stocked', 'all')


class ShoppingConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ShoppingSection(ShoppingConfig):
    id: UUID
    name: str
    rank: float
    created_ts: dt.datetime


class ShoppingSectionCreate(ShoppingConfig):
    name: ShoppingName


class ShoppingSectionUpdate(ShoppingConfig):
    name: NotNull[ShoppingName] = None


class ShoppingSectionRankMove(ShoppingConfig):
    """Place a section immediately before or after another."""

    before: ShoppingSectionRef | None = None
    after: ShoppingSectionRef | None = None

    @model_validator(mode='after')
    def exactly_one_neighbor(self):
        if (self.before is None) == (self.after is None):
            raise ValueError('give exactly one of before or after')
        return self


class ShoppingItem(ShoppingConfig):
    """`purchase_count` and `last_purchased_ts` are read from the purchase log."""

    id: UUID
    name: str
    note: str | None
    section_id: UUID | None
    section_name: str | None
    rank: float
    is_needed: bool
    needed_ts: dt.datetime | None
    created_ts: dt.datetime
    purchase_count: int
    last_purchased_ts: dt.datetime | None


class ShoppingItemCreate(ShoppingConfig):
    """Put a name on the list, creating it in the catalog only when it is new.

    `section` omitted keeps a known item where it was and puts a new one in
    Unsorted. `section` null puts either in Unsorted. A note is added to whatever note the item already carries while it
    is on the list, so two recipes asking for onions both stay readable.
    """

    name: ShoppingName
    note: str | None = None
    section: ShoppingSectionRef | None = None


class ShoppingItemUpdate(ShoppingConfig):
    """`section` null moves the item to Unsorted. `is_needed` false takes it off the list without a purchase."""

    name: NotNull[ShoppingName] = None
    note: str | None = None
    section: ShoppingSectionRef | None = None
    is_needed: NotNull[bool] = None


class ShoppingItemRankMove(ShoppingConfig):
    """Move an item into `section` (null is Unsorted), beside one neighbor or at the end.

    `section` is required because a drag always lands somewhere. With no
    neighbor the item goes last, which is what dropping into an empty section
    or below its last row means.
    """

    section: ShoppingSectionRef | None
    before: ShoppingItemRef | None = None
    after: ShoppingItemRef | None = None

    @model_validator(mode='after')
    def at_most_one_neighbor(self):
        if self.before is not None and self.after is not None:
            raise ValueError('give one of before or after, not both')
        return self


class ShoppingPurchase(ShoppingConfig):
    id: UUID
    item_id: UUID | None
    item_name: str
    note: str | None
    section_name: str | None
    purchased_ts: dt.datetime
