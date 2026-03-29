"""Seed durations with notes, covering active and completed periods."""

from __future__ import annotations

import random
from datetime import date
from datetime import timedelta

import sqlalchemy
from sqlalchemy.orm import Session

from ichrisbirch.models.duration import Duration
from ichrisbirch.models.duration_note import DurationNote
from scripts.seed.base import SeedResult

DURATIONS = [
    ('Portland apartment lease', 'Living in the Pearl District', '#4A90D9'),
    ('Python learning journey', 'Started with basics, now deep into async', '#50C878'),
    ('Home renovation project', None, '#D4A574'),
    ('Job search period', 'Focused on platform engineering roles', '#FF6B6B'),
    ('Training for half marathon', None, '#FFD700'),
    ('Reading challenge 2025', 'Goal: 24 books', '#9B59B6'),
]

NOTE_CONTENT = [
    'Made significant progress today',
    'Hit a plateau, need to reassess approach',
    'Milestone reached ahead of schedule',
    'Unexpected setback, adjusting timeline',
    'Found a great resource that accelerated learning',
    'Taking a short break to avoid burnout',
]


def clear(session: Session) -> None:
    session.execute(sqlalchemy.text('DELETE FROM duration_notes'))
    session.execute(sqlalchemy.text('DELETE FROM durations'))


def seed(session: Session, scale: int = 1) -> SeedResult:
    durations = []
    note_count = 0

    for rep in range(scale):
        for i, (name, notes, color) in enumerate(DURATIONS):
            title = name if scale == 1 else f'{name} #{rep + 1}'
            start = date.today() - timedelta(days=random.randint(60, 730))

            # ~50% completed (have end_date), ~50% active
            if i % 2 == 0:
                end = start + timedelta(days=random.randint(30, 365))
                if end > date.today():
                    end = date.today() - timedelta(days=random.randint(1, 10))
            else:
                end = None

            duration = Duration(
                name=title,
                start_date=start,
                end_date=end,
                notes=notes,
                color=color,
            )
            durations.append(duration)

    session.add_all(durations)
    session.flush()

    # Add notes to some durations
    for duration in durations:
        num_notes = random.randint(0, 3)
        for j in range(num_notes):
            note_date = duration.start_date + timedelta(days=random.randint(1, 60))
            if duration.end_date and note_date > duration.end_date:
                note_date = duration.end_date
            session.add(
                DurationNote(
                    duration_id=duration.id,
                    date=note_date,
                    content=NOTE_CONTENT[j % len(NOTE_CONTENT)],
                )
            )
            note_count += 1

    session.flush()

    active = sum(1 for d in durations if d.end_date is None)
    return SeedResult(
        model='Duration',
        count=len(durations),
        details=f'{active} active, {len(durations) - active} completed, {note_count} notes',
    )
