"""Seed tasks across all categories with realistic names and varied states."""

from __future__ import annotations

import random
from datetime import UTC
from datetime import datetime
from datetime import timedelta

import sqlalchemy
from sqlalchemy.orm import Session

from ichrisbirch.models.task import Task
from scripts.seed.base import SeedResult

TASKS_BY_CATEGORY = {
    'Automotive': [
        'Change oil in car',
        'Replace windshield wipers',
        'Get car inspected',
        'Rotate tires',
    ],
    'Chore': [
        'Clean bathroom',
        'Vacuum living room',
        'Organize closet',
        'Deep clean oven',
    ],
    'Computer': [
        'Backup external drive',
        'Update operating system',
        'Clean keyboard',
        'Compare VPN services',
    ],
    'Dingo': [
        'Walk Dingo',
        'Dingo vet appointment',
        'Buy Dingo food',
    ],
    'Financial': [
        'File quarterly taxes',
        'Review investment portfolio',
        'Update budget spreadsheet',
    ],
    'Home': [
        'Fix leaky faucet',
        'Replace air filter',
        'Touch up paint in hallway',
    ],
    'Kitchen': [
        'Sharpen knives',
        'Organize spice rack',
    ],
    'Learn': [
        'Complete Python course chapter',
        'Read database internals article',
        'Practice vim keybindings',
    ],
    'Personal': [
        'Schedule dentist appointment',
        'Renew passport',
        'Update emergency contacts',
    ],
    'Purchase': [
        'Buy new running shoes',
        'Order replacement light bulbs',
        'Get new bath towels',
    ],
    'Research': [
        'Research standing desk options',
        'Look into meal prep services',
    ],
    'Work': [
        'Update resume',
        'Prepare quarterly presentation',
        'Review project timeline',
    ],
}

NOTES = [
    'Need to finish this before the weekend',
    'Been putting this off for too long',
    'Should take about an hour',
    'Check YouTube for tutorial first',
    'Ask neighbor for recommendations',
]


def clear(session: Session) -> None:
    session.execute(sqlalchemy.text('DELETE FROM tasks'))


def seed(session: Session, scale: int = 1) -> SeedResult:
    tasks = []
    completed_count = 0

    for category, names in TASKS_BY_CATEGORY.items():
        for rep in range(scale):
            for i, name in enumerate(names):
                title = name if scale == 1 else f'{name} #{rep + 1}'
                notes = NOTES[i % len(NOTES)] if i % 3 != 0 else None
                priority = random.randint(1, 50)

                task = Task(
                    name=title,
                    category=category,
                    priority=priority,
                    notes=notes,
                )

                # ~20% completed (last task in each category)
                if i == len(names) - 1:
                    task.complete_date = datetime.now(UTC) - timedelta(days=random.randint(1, 30))
                    completed_count += 1

                tasks.append(task)

    session.add_all(tasks)
    session.flush()

    active = len(tasks) - completed_count
    return SeedResult(
        model='Task',
        count=len(tasks),
        details=f'{active} active, {completed_count} completed, {len(TASKS_BY_CATEGORY)} categories',
    )
