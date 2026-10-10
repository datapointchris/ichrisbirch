"""The shopping list: sections, a catalog of items, and a log of what was bought.

An item is a catalog row that outlives the trip. `is_needed` is whether it is on
the list now, and checking it off clears that rather than deleting the row, so
adding the same name again returns it to the section and the place it held.
Items off the list keep their `rank` for that reason, which is why the order is
a fractional rank: an integer position would leave gaps no client can see.

A purchase copies the item's name, note and section at the moment it was bought,
so the log reads the same after the item is renamed, moved or forgotten.
"""

from __future__ import annotations

import datetime as dt
from uuid import UUID
from uuid import uuid7

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Text
from sqlalchemy import Uuid
from sqlalchemy import func
from sqlalchemy import text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from ichrisbirch.database.base import Base
from ichrisbirch.database.fractionally_ranked import FractionallyRanked


class ShoppingSection(FractionallyRanked, Base):
    __tablename__ = 'sections'
    __table_args__ = (
        Index('uq_shopping_sections_name_folded', func.lower(text('name')), unique=True),
        Index('ix_shopping_sections_rank', 'rank'),
        {'schema': 'shopping'},
    )

    name: Mapped[str] = mapped_column(Text, nullable=False)

    items: Mapped[list[ShoppingItem]] = relationship('ShoppingItem', back_populates='section', passive_deletes=True)

    def __repr__(self) -> str:
        return f'ShoppingSection(name={self.name!r}, rank={self.rank!r})'


class ShoppingItem(FractionallyRanked, Base):
    __tablename__ = 'items'
    __table_args__ = (
        Index('uq_shopping_items_name_folded', func.lower(text('name')), unique=True),
        Index('ix_shopping_items_rank', 'rank'),
        Index('ix_shopping_items_is_needed', 'is_needed'),
        {'schema': 'shopping'},
    )

    name: Mapped[str] = mapped_column(Text, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Null is Unsorted, which is where a section's items go when it is deleted.
    section_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey('shopping.sections.id', ondelete='SET NULL'), nullable=True, index=True
    )
    is_needed: Mapped[bool] = mapped_column(nullable=False, server_default=text('true'))
    needed_ts: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    section: Mapped[ShoppingSection | None] = relationship('ShoppingSection', back_populates='items')
    purchases: Mapped[list[ShoppingPurchase]] = relationship('ShoppingPurchase', back_populates='item', passive_deletes=True)

    def __repr__(self) -> str:
        return f'ShoppingItem(name={self.name!r}, is_needed={self.is_needed!r})'


class ShoppingPurchase(Base):
    __tablename__ = 'purchases'
    __table_args__ = (
        Index('ix_shopping_purchases_purchased_ts', 'purchased_ts'),
        {'schema': 'shopping'},
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    # Null once the item is forgotten. The snapshot columns keep the record whole.
    item_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey('shopping.items.id', ondelete='SET NULL'), nullable=True, index=True)
    item_name: Mapped[str] = mapped_column(Text, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    section_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    purchased_ts: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))

    item: Mapped[ShoppingItem | None] = relationship('ShoppingItem', back_populates='purchases')

    def __repr__(self) -> str:
        return f'ShoppingPurchase(item_name={self.item_name!r}, purchased_ts={self.purchased_ts!r})'
