"""Seed events with a mix of past and upcoming dates."""

from __future__ import annotations

import random
from datetime import UTC
from datetime import datetime
from datetime import timedelta

import sqlalchemy
from sqlalchemy.orm import Session

from ichrisbirch.models.event import Event
from scripts.seed.base import SeedResult

# (name, venue, cost)
EVENTS = [
    ('Portland Jazz Festival', 'Pioneer Courthouse Square', 45.00),
    ('Python Portland Meetup', 'Puppet Labs', 0.00),
    ('Comedy Show at Helium', 'Helium Comedy Club', 25.00),
    ('Neighborhood Block Party', 'SE Division Street', 0.00),
    ('Wine Tasting Tour', 'Willamette Valley', 65.00),
    ('Tech Talk on Kubernetes', 'New Relic HQ', 0.00),
    ('Art Gallery Opening', 'Portland Art Museum', 15.00),
    ('Board Game Night', 'Guardian Games', 10.00),
    ('PyCon US 2026', 'Pittsburgh Convention Center', 400.00),
    ('Local Food Market', 'PSU Farmers Market', 0.00),
    ('Concert at Doug Fir', 'Doug Fir Lounge', 30.00),
    ('Dentist Checkup', 'Pearl District Dental', 150.00),
    ('Trail Run 10K', 'Forest Park', 35.00),
    ('Friends Wedding', 'McMenamins Edgefield', 0.00),
    ('AWS re:Invent', 'Las Vegas Convention Center', 1800.00),
]

NOTES = [
    "Don't forget to RSVP",
    'Bring a friend',
    'Need to book hotel',
    'Carpooling with Mike',
    None,
]


def clear(session: Session) -> None:
    session.execute(sqlalchemy.text('DELETE FROM events'))


def seed(session: Session, scale: int = 1) -> SeedResult:
    events = []
    past_count = 0

    for rep in range(scale):
        for i, (name, venue, cost) in enumerate(EVENTS):
            title = name if scale == 1 else f'{name} #{rep + 1}'
            # ~30% past events, ~70% upcoming
            if i % 3 == 0:
                event_date = datetime.now(UTC) - timedelta(days=random.randint(7, 180))
                past_count += 1
            else:
                event_date = datetime.now(UTC) + timedelta(days=random.randint(7, 365))

            events.append(
                Event(
                    name=title,
                    date=event_date,
                    venue=venue,
                    url=f'https://example.com/event/{i + rep * len(EVENTS)}' if i % 4 != 0 else None,
                    cost=cost,
                    attending=i % 5 != 0,
                    notes=NOTES[i % len(NOTES)],
                )
            )

    session.add_all(events)
    session.flush()

    upcoming = len(events) - past_count
    return SeedResult(
        model='Event',
        count=len(events),
        details=f'{past_count} past, {upcoming} upcoming',
    )
