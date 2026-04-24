from datetime import datetime

from ichrisbirch.models.task import Task

BASE_DATA: list[Task] = [
    Task(
        name='Task 1 Chore with notes priority 1 not completed',
        notes='Notes for task 1',
        category='Chore',
        priority=1,
    ),
    Task(
        name='Task 2 Home without notes priority 2 not completed',
        notes=None,
        category='Home',
        priority=2,
    ),
    Task(
        name='Task 3 Home with notes priority 3 completed',
        notes='Notes for task 3',
        category='Home',
        priority=3,
        complete_date=datetime(2020, 4, 20, 3, 3, 39, 50648).isoformat(),
    ),
]
