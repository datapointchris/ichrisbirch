"""Seed a shopping list mid-week: a few sections, a list to shop, and a catalog with history.

Most catalog items are off the list and carry purchases, which is what feeds
"Buy again". Two items sit in Unsorted, the way a quick add from the phone lands.
"""

from __future__ import annotations

import datetime as dt
import random

import sqlalchemy as sa
from sqlalchemy.orm import Session

from ichrisbirch.models.shopping import ShoppingItem
from ichrisbirch.models.shopping import ShoppingPurchase
from ichrisbirch.models.shopping import ShoppingSection
from scripts.seed.base import SeedResult
from scripts.seed.base import random_past_datetime

# Section name, then (item, note, on the list now) in aisle order.
CATALOG: list[tuple[str, list[tuple[str, str | None, bool]]]] = [
    (
        'Costco',
        [
            ('eggs', '2 dozen', True),
            ('paper towels', None, True),
            ('coffee beans', None, False),
            ('olive oil', None, False),
            ('frozen berries', None, True),
        ],
    ),
    (
        'Grocery',
        [
            ('bananas', None, True),
            ('yellow onion', '3', True),
            ('milk', None, False),
            ('butter', 'unsalted', False),
            ('tamari', None, False),
            ('cilantro', None, False),
        ],
    ),
    (
        'Hardware',
        [
            ('wood glue', None, True),
            ('furnace filter', '16x25x1', False),
        ],
    ),
    (
        'Online',
        [
            ('camping mattress', None, True),
            ('cordless vacuum', None, False),
        ],
    ),
]

UNSORTED: list[tuple[str, str | None]] = [
    ('hot plate for glue', None),
    ('clothes hamper', None),
]


def clear(session: Session) -> None:
    session.execute(sa.text('DELETE FROM shopping.purchases'))
    session.execute(sa.text('DELETE FROM shopping.items'))
    session.execute(sa.text('DELETE FROM shopping.sections'))


def purchases_for(item: ShoppingItem, section: ShoppingSection | None, times: int) -> list[ShoppingPurchase]:
    return [
        ShoppingPurchase(
            item=item,
            item_name=item.name,
            section_name=section.name if section else None,
            purchased_ts=random_past_datetime(120),
        )
        for _ in range(times)
    ]


def seed(session: Session, scale: int = 1) -> SeedResult:
    now = dt.datetime.now(dt.UTC)
    sections: list[ShoppingSection] = []
    items: list[ShoppingItem] = []
    purchases: list[ShoppingPurchase] = []
    rank = 0.0

    for section_rank, (section_name, entries) in enumerate(CATALOG, start=1):
        section = ShoppingSection(name=section_name, rank=float(section_rank))
        sections.append(section)
        for name, note, needed in entries:
            rank += 1.0
            item = ShoppingItem(
                name=name,
                note=note,
                section=section,
                rank=rank,
                is_needed=needed,
                needed_ts=now - dt.timedelta(days=random.randint(0, 6)) if needed else None,
            )
            items.append(item)
            purchases += purchases_for(item, section, random.randint(0 if needed else 1, 6))

    for name, note in UNSORTED:
        rank += 1.0
        items.append(ShoppingItem(name=name, note=note, rank=rank, is_needed=True, needed_ts=now))

    for i in range((scale - 1) * 10):
        rank += 1.0
        section = random.choice(sections)
        item = ShoppingItem(name=f'Test item #{i + 1}', section=section, rank=rank, is_needed=random.random() < 0.3)
        items.append(item)
        purchases += purchases_for(item, section, random.randint(0, 4))

    session.add_all(sections)
    session.add_all(items)
    session.add_all(purchases)
    session.flush()
    return SeedResult(
        model='ShoppingItem',
        count=len(items),
        details=f'{len(sections)} sections, {sum(item.is_needed for item in items)} on the list, {len(purchases)} purchases',
    )
