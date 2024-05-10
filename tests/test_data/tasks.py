from datetime import datetime

from ichrisbirch.models.task import Task
from ichrisbirch.models.task import TaskCategory

BASE_DATA: list[Task] = [
    Task(
        name='Task 1 Chore with notes priority 5 not completed',
        notes='Notes for task 1',
        category=TaskCategory.Chore.value,
        priority=5,
    ),
    Task(
        name='Task 2 Home without notes priority 10 not completed',
        notes=None,
        category=TaskCategory.Home.value,
        priority=10,
    ),
    Task(
        name='Task 3 Home with notes priority 15 completed',
        notes='Notes for task 3',
        category=TaskCategory.Home.value,
        priority=15,
        complete_date=datetime(2020, 4, 20, 3, 3, 39, 50648).isoformat(),
    ),
]
