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
        'Check tire pressure',
        'Replace cabin air filter',
        'Wash and wax car',
        'Replace brake pads',
    ],
    'Chore': [
        'Clean bathroom',
        'Vacuum living room',
        'Organize closet',
        'Deep clean oven',
        'Mop kitchen floor',
        'Clean gutters',
        'Wash windows',
        'Declutter garage',
        'Sort recycling',
        'Iron shirts',
    ],
    'Computer': [
        'Backup external drive',
        'Update operating system',
        'Clean keyboard',
        'Compare VPN services',
        'Set up automated backups',
        'Reinstall development tools',
        'Update dotfiles',
        'Clean up Docker images',
    ],
    'Dingo': [
        'Walk Dingo',
        'Dingo vet appointment',
        'Buy Dingo food',
        'Trim Dingo nails',
        'Dingo flea treatment',
        'Buy new dog toys',
    ],
    'Financial': [
        'File quarterly taxes',
        'Review investment portfolio',
        'Update budget spreadsheet',
        'Pay property tax',
        'Review insurance policies',
        'Reconcile bank statements',
        'Set up automatic savings',
    ],
    'Home': [
        'Fix leaky faucet',
        'Replace air filter',
        'Touch up paint in hallway',
        'Caulk bathroom tiles',
        'Fix squeaky door hinge',
        'Replace smoke detector batteries',
        'Organize tool shelf',
        'Patch drywall hole',
    ],
    'Kitchen': [
        'Sharpen knives',
        'Organize spice rack',
        'Deep clean refrigerator',
        'Replace water filter',
        'Season cast iron pan',
        'Organize pantry',
    ],
    'Learn': [
        'Complete Python course chapter',
        'Read database internals article',
        'Practice vim keybindings',
        'Study Kubernetes networking',
        'Read DDIA chapter',
        'Watch systems design lecture',
        'Complete Go tutorial',
        'Study SQLAlchemy docs',
    ],
    'Personal': [
        'Schedule dentist appointment',
        'Renew passport',
        'Update emergency contacts',
        'Get haircut',
        'Schedule eye exam',
        'Organize photo library',
        'Update address book',
    ],
    'Purchase': [
        'Buy new running shoes',
        'Order replacement light bulbs',
        'Get new bath towels',
        'Buy surge protector',
        'Order HDMI cables',
        'Get new water bottle',
    ],
    'Research': [
        'Research standing desk options',
        'Look into meal prep services',
        'Compare cloud storage plans',
        'Research ergonomic keyboards',
        'Evaluate note-taking apps',
        'Compare home security systems',
    ],
    'Work': [
        'Update resume',
        'Prepare quarterly presentation',
        'Review project timeline',
        'Write performance self-review',
        'Organize work documentation',
        'Update LinkedIn profile',
        'Clean up Jira backlog',
    ],
}

NOTES = [
    'Need to finish this before the weekend',
    'Been putting this off for too long',
    'Should take about an hour',
    'Check YouTube for tutorial first',
    'Ask neighbor for recommendations',
    'Higher priority than it looks',
    'Blocked until parts arrive',
    'Can do this while watching TV',
    'Need to schedule a full afternoon',
    'Quick 15-minute job',
]


def clear(session: Session) -> None:
    session.execute(sqlalchemy.text('DELETE FROM autofun_active_tasks'))
    session.execute(sqlalchemy.text('DELETE FROM tasks'))


def seed(session: Session, scale: int = 1) -> SeedResult:
    tasks = []
    completed_count = 0
    now = datetime.now(UTC)

    for category, names in TASKS_BY_CATEGORY.items():
        for rep in range(scale):
            for i, name in enumerate(names):
                title = name if scale == 1 else f'{name} #{rep + 1}'
                notes = NOTES[i % len(NOTES)] if random.random() < 0.4 else None
                priority = random.randint(1, 50)

                # Spread add_date across the last 18 months for realistic history
                days_ago = random.randint(1, 540)
                add_date = now - timedelta(days=days_ago)

                task = Task(
                    name=title,
                    category=category,
                    priority=priority,
                    notes=notes,
                    add_date=add_date,
                )

                # ~60% completed — with varied completion times per category
                if random.random() < 0.6:
                    # Completion time varies by category to make avg-time chart interesting
                    if category in ('Chore', 'Kitchen', 'Purchase'):
                        completion_days = random.randint(1, 14)
                    elif category in ('Financial', 'Work', 'Research'):
                        completion_days = random.randint(7, 90)
                    elif category in ('Learn', 'Computer'):
                        completion_days = random.randint(14, 120)
                    elif category in ('Home', 'Automotive'):
                        completion_days = random.randint(3, 60)
                    else:
                        completion_days = random.randint(1, 45)

                    complete_date = add_date + timedelta(days=completion_days)
                    # Don't complete tasks in the future
                    if complete_date <= now:
                        task.complete_date = complete_date
                        completed_count += 1
                    else:
                        # Leave as outstanding — these become the "recent" outstanding tasks
                        pass
                else:
                    # Outstanding tasks — some overdue (negative priority)
                    if random.random() < 0.2:
                        task.priority = random.randint(-10, -1)

                tasks.append(task)

    # Guarantee tasks in each priority band for frontend badge visibility
    # Vue store: overdue (< 1), critical (1-2), due_soon (3-5)
    outstanding = [t for t in tasks if t.complete_date is None]
    band_targets = [
        (lambda t: t.priority < 1, -5, 'overdue'),
        (lambda t: 1 <= t.priority <= 2, 2, 'critical'),
        (lambda t: 3 <= t.priority <= 5, 4, 'due_soon'),
    ]
    for check_fn, target_priority, _label in band_targets:
        in_band = sum(1 for t in outstanding if check_fn(t))
        if in_band < 2:
            # Move some high-priority outstanding tasks into this band
            candidates = [t for t in outstanding if t.priority > 5 and not check_fn(t)]
            for t in candidates[: 2 - in_band]:
                t.priority = target_priority

    session.add_all(tasks)
    session.flush()

    active = len(tasks) - completed_count
    return SeedResult(
        model='Task',
        count=len(tasks),
        details=f'{active} active, {completed_count} completed, {len(TASKS_BY_CATEGORY)} categories',
    )
