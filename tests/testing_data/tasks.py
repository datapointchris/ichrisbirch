from datetime import datetime
from typing import Any

from ichrisbirch.models.task import TaskCategory

TASK_TEST_DATA: list[dict[str, Any]] = [
    {
        'name': 'Task 1 Chore with notes priority 5 not completed',
        'notes': 'Notes for task 1',
        'category': TaskCategory.Chore.value,
        'priority': 5,
    },
    {
        'name': 'Task 2 Home without notes priority 10 not completed',
        'notes': None,
        'category': TaskCategory.Home.value,
        'priority': 10,
    },
    {
        'name': 'Task 3 Home with notes priority 15 completed',
        'notes': 'Notes for task 3',
        'category': TaskCategory.Home.value,
        'priority': 15,
        'complete_date': datetime(2020, 4, 20, 3, 3, 39, 50648).isoformat(),
    },
]

TASK_TEST_CREATE_DATA = {
    'name': 'Task 4 Computer with notes priority 3',
    'notes': 'Notes task 4',
    'category': TaskCategory.Computer.value,
    'priority': 3,
}
