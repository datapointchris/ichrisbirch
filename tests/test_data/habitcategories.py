from datetime import datetime

from ichrisbirch.models.habit import Habit
from ichrisbirch.models.habitcategory import HabitCategory
from ichrisbirch.models.habitcompleted import HabitCompleted

BASE_DATA: list[HabitCategory] = [
    HabitCategory(
        name='Category 1',
        is_current=True,
    ),
    HabitCategory(
        name='Category 2',
        is_current=True,
        habits=[
            Habit(name='Habit 1 Category 2', is_current=True),
            Habit(name='Habit 3 Category 2', is_current=False),
        ],
        completed_habits=[
            HabitCompleted(name='Completed Habit 3 Category 2', complete_date=datetime(2024, 1, 3)),
        ],
    ),
    HabitCategory(
        name='Category 3',
        is_current=False,
        habits=[
            Habit(name='Habit 2 Category 3', is_current=True),
        ],
        completed_habits=[
            HabitCompleted(name='Completed Habit 1 Category 3', complete_date=datetime(2024, 1, 1)),
            HabitCompleted(name='Completed Habit 2 Category 3', complete_date=datetime(2024, 1, 2)),
        ],
    ),
]
