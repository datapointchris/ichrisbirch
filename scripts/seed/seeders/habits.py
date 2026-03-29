"""Seed habit categories, habits, and completion records."""

from __future__ import annotations

import random
from datetime import UTC
from datetime import datetime
from datetime import timedelta

import sqlalchemy
from sqlalchemy.orm import Session

from ichrisbirch.models.habit import Habit
from ichrisbirch.models.habitcategory import HabitCategory
from ichrisbirch.models.habitcompleted import HabitCompleted
from scripts.seed.base import SeedResult

CATEGORIES = [
    ('Exercise', True),
    ('Reading', True),
    ('Meditation', True),
    ('Coding', True),
    ('Music', True),
    ('Nutrition', True),
    ('Journaling', False),
    ('Drawing', False),
]

# (name, category_name, is_current)
HABITS = [
    ('Morning run', 'Exercise', True),
    ('Strength training', 'Exercise', True),
    ('Read 30 minutes', 'Reading', True),
    ('Review saved articles', 'Reading', True),
    ('10 minute meditation', 'Meditation', True),
    ('Breathing exercises', 'Meditation', False),
    ('LeetCode problem', 'Coding', True),
    ('Open source contribution', 'Coding', False),
    ('Practice guitar', 'Music', True),
    ('Music theory study', 'Music', True),
]


def clear(session: Session) -> None:
    session.execute(sqlalchemy.text('DELETE FROM habits.completed'))
    session.execute(sqlalchemy.text('DELETE FROM habits.habits'))
    session.execute(sqlalchemy.text('DELETE FROM habits.categories'))


def seed(session: Session, scale: int = 1) -> SeedResult:
    # Create categories
    categories = []
    cat_map: dict[str, HabitCategory] = {}
    for name, is_current in CATEGORIES:
        cat = HabitCategory(name=name, is_current=is_current)
        categories.append(cat)
    session.add_all(categories)
    session.flush()

    for cat in categories:
        cat_map[cat.name] = cat

    # Create habits
    habits = []
    for rep in range(scale):
        for name, cat_name, is_current in HABITS:
            habit_name = name if scale == 1 else f'{name} #{rep + 1}'
            habits.append(
                Habit(
                    name=habit_name,
                    category_id=cat_map[cat_name].id,
                    is_current=is_current,
                )
            )
    session.add_all(habits)
    session.flush()

    # Create completion records for current habits
    completions = []
    for habit in habits:
        if not habit.is_current:
            continue
        num_completions = random.randint(1, 3) * scale
        for _ in range(num_completions):
            complete_date = datetime.now(UTC) - timedelta(days=random.randint(1, 60))
            completions.append(
                HabitCompleted(
                    name=habit.name,
                    category_id=habit.category_id,
                    complete_date=complete_date,
                )
            )

    session.add_all(completions)
    session.flush()

    current = sum(1 for h in habits if h.is_current)
    return SeedResult(
        model='Habit',
        count=len(categories) + len(habits) + len(completions),
        details=f'{len(categories)} categories, {len(habits)} habits ({current} current), {len(completions)} completions',
    )
