"""Seed countdowns with a mix of near-term and far-future due dates."""

from __future__ import annotations

import random
from datetime import date
from datetime import timedelta

import sqlalchemy
from sqlalchemy.orm import Session

from ichrisbirch.models.countdown import Countdown
from scripts.seed.base import SeedResult

COUNTDOWNS = [
    ('PyCon US 2026', 'Registration confirmed, hotel booked'),
    ('Vacation to Japan', 'Need to finalize itinerary'),
    ('Lease Renewal', None),
    ('Project Launch', 'All features must be complete'),
    ('Birthday Party', None),
    ('Tax Deadline', 'Gather W-2 and 1099 forms'),
    ('Concert Tickets', None),
    ('Dentist Appointment', 'Already happened, need to reschedule'),
    ('Insurance Renewal', None),
]


def clear(session: Session) -> None:
    session.execute(sqlalchemy.text('DELETE FROM countdowns'))


def seed(session: Session, scale: int = 1) -> SeedResult:
    countdowns = []
    for rep in range(scale):
        for i, (name, notes) in enumerate(COUNTDOWNS):
            title = name if scale == 1 else f'{name} #{rep + 1}'
            # Spread due dates: some overdue, some near, some far
            if i >= 7:
                # Last 2 items are overdue (past due dates)
                due = date.today() - timedelta(days=random.randint(3, 30))
            elif i % 2 == 0:
                due = date.today() + timedelta(days=random.randint(7, 30))
            else:
                due = date.today() + timedelta(days=random.randint(60, 365))
            countdowns.append(Countdown(name=title, notes=notes, due_date=due))

    session.add_all(countdowns)
    session.flush()

    overdue = sum(1 for c in countdowns if c.due_date < date.today())
    near = sum(1 for c in countdowns if 0 <= (c.due_date - date.today()).days <= 30)
    far = len(countdowns) - overdue - near
    return SeedResult(
        model='Countdown',
        count=len(countdowns),
        details=f'{overdue} overdue, {near} near-term, {far} far-future',
    )
