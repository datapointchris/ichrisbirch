"""Seed patterns with observations spread across recent weeks."""

from __future__ import annotations

import random
from datetime import UTC
from datetime import datetime
from datetime import timedelta

import sqlalchemy
from sqlalchemy.orm import Session

from ichrisbirch.models.pattern import Pattern
from scripts.seed.base import SeedResult

MESSAGES = [
    'coffee around 3pm, wired until midnight',
    'slight heartburn after the soy sauce again',
    'right calf stiff, probably from sitting sideways all afternoon',
    'sleepy but I cannot stop wanting to be on the computer',
    'worked on it first thing and it was done by lunch',
    'skipped breakfast, snappy by 11am',
    'walked after dinner and slept straight through',
    'third night in a row under six hours',
    'ate late, woke up at 4am',
]


def clear(session: Session) -> None:
    session.execute(sqlalchemy.text('DELETE FROM patterns'))


def seed(session: Session, scale: int = 1) -> SeedResult:
    now = datetime.now(UTC)
    patterns = []
    for rep in range(scale):
        for i, message in enumerate(MESSAGES):
            text = message if scale == 1 else f'{message} (#{rep + 1})'
            # Spread backwards over roughly two months so correlation over time
            # has something to work with.
            recorded_at = now - timedelta(days=i * 6 + rep * 2, hours=random.randint(0, 23))
            patterns.append(Pattern(message=text, recorded_at=recorded_at))

    session.add_all(patterns)
    session.flush()

    oldest = min(p.recorded_at for p in patterns)
    span_days = (now - oldest).days
    return SeedResult(model='Pattern', count=len(patterns), details=f'spanning {span_days} days')
