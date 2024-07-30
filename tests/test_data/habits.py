from ichrisbirch.models.habit import Habit

BASE_DATA: list[Habit] = [
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
