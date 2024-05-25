from datetime import datetime

from ichrisbirch.models.habit import Habit
from ichrisbirch.models.habit import HabitCategory
from ichrisbirch.models.habit import HabitCompleted

HABIT_CATEGORIES: list[HabitCategory] = [
    HabitCategory(
        name='Category 1',
        is_current=True,
    ),
    HabitCategory(
        name='Category 2',
        is_current=True,
    ),
    HabitCategory(
        name='Category 3',
        is_current=False,
    ),
]


HABITS: list[Habit] = [
    Habit(
        name='Habit 1 Category Id 2',
        category_id=2,
        is_current=True,
    ),
    Habit(
        name='Habit 2 Category Id 3',
        category_id=3,
        is_current=True,
    ),
    Habit(
        name='Habit 3 Category Id 2',
        category_id=2,
        is_current=False,
    ),
]

COMPLETED_HABITS: list[HabitCompleted] = [
    HabitCompleted(
        name='Completed Habit 1 Category Id 3',
        category_id=3,
        complete_date=datetime(2024, 1, 1),
    ),
    HabitCompleted(
        name='Completed Habit 2 Category Id 3',
        category_id=3,
        complete_date=datetime(2024, 1, 2),
    ),
    HabitCompleted(
        name='Completed Habit 3 Category Id 2',
        category_id=2,
        complete_date=datetime(2024, 1, 3),
    ),
]

BASE_DATA = HABIT_CATEGORIES + HABITS + COMPLETED_HABITS
