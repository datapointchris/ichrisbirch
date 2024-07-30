from datetime import datetime

from ichrisbirch.models.habitcompleted import HabitCompleted

BASE_DATA: list[HabitCompleted] = [
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
