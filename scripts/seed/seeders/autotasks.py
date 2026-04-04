"""Seed autotasks covering all frequencies with realistic maintenance tasks."""

from __future__ import annotations

import random
from datetime import UTC
from datetime import datetime
from datetime import timedelta

import sqlalchemy
from sqlalchemy.orm import Session

from ichrisbirch.models.autotask import AutoTask
from scripts.seed.base import SeedResult

# (name, category, frequency)
AUTOTASKS = [
    ('Vacuum house', 'Chore', 'Weekly'),
    ('Clean kitchen', 'Chore', 'Daily'),
    ('Water plants', 'Home', 'Biweekly'),
    ('Take out trash', 'Chore', 'Biweekly'),
    ('Do laundry', 'Chore', 'Weekly'),
    ('Clean bathroom', 'Chore', 'Monthly'),
    ('Mop floors', 'Chore', 'Monthly'),
    ('Dust furniture', 'Chore', 'Monthly'),
    ('Clean fridge', 'Kitchen', 'Quarterly'),
    ('Change bed sheets', 'Chore', 'Biweekly'),
    ('Check smoke detectors', 'Home', 'Semiannually'),
    ('Clean gutters', 'Home', 'Semiannually'),
    ('Service HVAC', 'Home', 'Yearly'),
    ('Rotate tires', 'Automotive', 'Yearly'),
]


def clear(session: Session) -> None:
    session.execute(sqlalchemy.text('DELETE FROM autotasks'))


def seed(session: Session, scale: int = 1) -> SeedResult:
    autotasks = []
    for rep in range(scale):
        for i, (name, category, frequency) in enumerate(AUTOTASKS):
            title = name if scale == 1 else f'{name} #{rep + 1}'
            # First 2 autotasks have never been run (run_count=0, last_run_date
            # defaults to creation time via server_default — don't override it)
            if i < 2:
                run_count = 0
                last_run = datetime.now(UTC)  # mimics server_default=now()
            else:
                run_count = random.randint(1, 20)
                # One autotask should be due today (last_run far enough ago for its frequency)
                if i == 2:
                    last_run = datetime.now(UTC) - timedelta(days=30)
                else:
                    last_run = datetime.now(UTC) - timedelta(days=random.randint(1, 60))

            autotasks.append(
                AutoTask(
                    name=title,
                    category=category,
                    frequency=frequency,
                    priority=random.randint(5, 40),
                    notes='Set reminder' if i % 3 == 0 else None,
                    max_concurrent=random.choice([1, 2, 2, 3]),
                    run_count=run_count,
                    last_run_date=last_run,
                )
            )

    session.add_all(autotasks)
    session.flush()

    freqs = {a.frequency for a in autotasks}
    return SeedResult(
        model='AutoTask',
        count=len(autotasks),
        details=f'{len(freqs)} frequencies covered',
    )
