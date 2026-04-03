"""Seed autofun with a variety of specific one-time fun activities."""

from __future__ import annotations

import sqlalchemy
from sqlalchemy.orm import Session

from ichrisbirch.models.autofun import AutoFun
from scripts.seed.base import SeedResult

AUTOFUN_ITEMS = [
    ('Visit the Japanese Tea Garden in Golden Gate Park', 'Free on weekday mornings before 10am'),
    ('Try the omakase at Hashiri in SoMa', None),
    ('Hike the Dipsea Trail from Mill Valley to Stinson Beach', '7.4 miles one way, take the bus back'),
    ('Watch a film at the Castro Theatre', 'Check their schedule for special screenings'),
    ('Take a kayak tour of the Bay under the Bay Bridge', None),
    ('Visit Alcatraz at sunset on a clear day', 'Book night tour tickets in advance'),
    ('Eat at Burma Superstar — get the tea leaf salad', 'Expect a wait, no reservations'),
    ('Drive to Point Reyes and hike to Chimney Rock', 'Great for whale watching in winter'),
    ('Catch a Giants game at Oracle Park', 'Sit in the bleachers for the bay view'),
    ('Do the Lands End coastal trail and stop at the ruins', 'Bring a jacket'),
    ('Try the lamb shoulder at Zuni Cafe', None),
    ('Visit the de Young Museum for a traveling exhibition', None),
    ('Take the ferry to Sausalito and bike back across the bridge', 'Rent bikes at the ferry terminal'),
    ('Walk the Embarcadero at low tide in the early morning', None),
    ('See a show at SFJAZZ', 'Check their lineup for the season'),
]


def clear(session: Session) -> None:
    session.execute(sqlalchemy.text('DELETE FROM autofun'))


def seed(session: Session, scale: int = 1) -> SeedResult:
    items = []
    for rep in range(scale):
        for name, notes in AUTOFUN_ITEMS:
            title = name if scale == 1 else f'{name} #{rep + 1}'
            items.append(AutoFun(name=title, notes=notes))

    session.add_all(items)
    session.flush()
    return SeedResult(model='AutoFun', count=len(items), details=f'{len(AUTOFUN_ITEMS)} unique activities')
