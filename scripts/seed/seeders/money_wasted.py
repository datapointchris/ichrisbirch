"""Seed money wasted entries with varied amounts."""

from __future__ import annotations

import random
from datetime import date
from datetime import timedelta

import sqlalchemy
from sqlalchemy.orm import Session

from ichrisbirch.models.money_wasted import MoneyWasted
from scripts.seed.base import SeedResult

ITEMS = [
    ('Gym membership never used', 49.99, 'Signed up in January, went twice'),
    ('Impulse Amazon purchase', 34.50, None),
    ('Expired groceries thrown out', 22.00, 'Forgot about the produce in the back of the fridge'),
    ('Uber instead of biking', 18.75, None),
    ('Premium app subscription', 12.99, 'Cancelled now'),
    ('Takeout when fridge was full', 28.00, 'Laziness tax'),
    ('Movie ticket for bad film', 15.50, None),
]


def clear(session: Session) -> None:
    session.execute(sqlalchemy.text('DELETE FROM money_wasted'))


def seed(session: Session, scale: int = 1) -> SeedResult:
    entries = []
    for rep in range(scale):
        for i, (item, amount, notes) in enumerate(ITEMS):
            name = item if scale == 1 else f'{item} #{rep + 1}'
            wasted = date.today() - timedelta(days=random.randint(1, 180))
            purchased = wasted - timedelta(days=random.randint(1, 30)) if i % 2 == 0 else None
            entries.append(
                MoneyWasted(
                    item=name,
                    amount=round(amount * random.uniform(0.8, 1.2), 2),
                    date_purchased=purchased,
                    date_wasted=wasted,
                    notes=notes,
                )
            )

    session.add_all(entries)
    session.flush()

    total_amount = sum(e.amount for e in entries)
    return SeedResult(
        model='MoneyWasted',
        count=len(entries),
        details=f'${total_amount:.2f} total wasted',
    )
