from ichrisbirch.models.habitcategory import HabitCategory

BASE_DATA: list[HabitCategory] = [
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
