from datetime import datetime

from ichrisbirch.models.task import Task, TaskCategory

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
# dict so it can be JSON serialized easily
CREATE_DATA = dict(
    name='Task 4 Computer with notes priority 3',
    notes='Notes task 4',
    category=TaskCategory.Computer.value,
    priority=3,
)
