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
    ('Learning', True),
    ('Wellness', True),
    ('Music', True),
    ('Productivity', False),
]

# (name, category_name, is_current, frequency)
# frequency: avg completions per week (higher = more consistent habit)
# Realistic: ~8 current habits across ~4 active categories
HABITS = [
    ('Morning run', 'Exercise', True, 4.0),
    ('Stretching', 'Exercise', True, 5.5),
    ('Read 30 minutes', 'Learning', True, 6.0),
    ('Duolingo lesson', 'Learning', True, 5.0),
    ('10 minute meditation', 'Wellness', True, 4.5),
    ('Take vitamins', 'Wellness', True, 6.0),
    ('Practice guitar', 'Music', True, 3.0),
    ('Ear training', 'Music', True, 2.0),
    ('Cold shower', 'Wellness', True, 0.0),
    ('Journal entry', 'Productivity', False, 1.5),
    ('Code review', 'Productivity', False, 0.5),
]


def clear(session: Session) -> None:
    session.execute(sqlalchemy.text('DELETE FROM habits.completed'))
    session.execute(sqlalchemy.text('DELETE FROM habits.habits'))
    session.execute(sqlalchemy.text('DELETE FROM habits.categories'))


def seed(session: Session, scale: int = 1) -> SeedResult:
    rng = random.Random(42)
    now = datetime.now(UTC)

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
        for name, cat_name, is_current, _freq in HABITS:
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

    # Generate completions spread over 18 months with realistic variation
    completions = []
    history_days = 540  # 18 months

    for habit in habits:
        _name, _cat, _current, freq = next((n, c, cur, f) for n, c, cur, f in HABITS if habit.name.startswith(n))

        # Non-current habits only have sparse old completions
        if not habit.is_current:
            num = rng.randint(3, 12) * scale
            for _ in range(num):
                days_ago = rng.randint(180, history_days)
                completions.append(
                    HabitCompleted(
                        name=habit.name,
                        category_id=habit.category_id,
                        complete_date=now - timedelta(days=days_ago, hours=rng.randint(6, 22)),
                    )
                )
            continue

        # Current habits: simulate week-by-week with frequency as probability
        # Add a per-habit consistency factor so some habits are more reliably done
        consistency = rng.uniform(0.5, 1.2)
        weekly_target = freq * consistency * scale

        for week in range(history_days // 7):
            week_start_days_ago = history_days - (week * 7)
            # Habits tend to be done more recently (ramp up over time)
            recency_boost = 0.6 + 0.4 * (week / (history_days // 7))
            actual_completions = int(weekly_target * recency_boost + rng.uniform(-0.5, 0.5))
            actual_completions = max(0, min(actual_completions, 7))

            # Randomly skip entire weeks occasionally (vacation, illness)
            if rng.random() < 0.08:
                continue

            for day_offset in rng.sample(range(7), min(actual_completions, 7)):
                days_ago = week_start_days_ago - day_offset
                if days_ago < 0:
                    continue
                completions.append(
                    HabitCompleted(
                        name=habit.name,
                        category_id=habit.category_id,
                        complete_date=now - timedelta(days=days_ago, hours=rng.randint(6, 22)),
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
