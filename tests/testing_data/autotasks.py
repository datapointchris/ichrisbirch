from datetime import datetime

from ichrisbirch.models.autotask import AutoTask, TaskFrequency
from ichrisbirch.models.task import TaskCategory

BASE_DATA: list[AutoTask] = [
    AutoTask(
        name='AutoTask 1 Chore with notes priority 5 not completed',
        notes='Notes for task 1',
        category=TaskCategory.Chore.value,
        priority=5,
        frequency=TaskFrequency.Daily.value,
        first_run_date=datetime(2020, 4, 20, 3, 3, 39, 50648).isoformat(),
        last_run_date=datetime(2020, 4, 24, 3, 3, 39, 50648).isoformat(),
        run_count=5,
    ),
    AutoTask(
        name='AutoTask 2 Home without notes priority 10 not completed',
        notes=None,
        category=TaskCategory.Home.value,
        priority=10,
        frequency=TaskFrequency.Weekly.value,
        first_run_date=datetime(2020, 3, 20, 3, 3, 39, 50648).isoformat(),
        last_run_date=datetime(2020, 3, 24, 3, 3, 39, 50648).isoformat(),
        run_count=1,
    ),
    AutoTask(
        name='AutoTask 3 Home with notes priority 15 completed',
        notes='Notes for task 3',
        category=TaskCategory.Home.value,
        priority=15,
        frequency=TaskFrequency.Quarterly.value,
        first_run_date=datetime(2020, 1, 20, 3, 3, 39, 50648).isoformat(),
        last_run_date=datetime(2020, 1, 24, 3, 3, 39, 50648).isoformat(),
        run_count=2,
    ),
]
# dict so it can be JSON serialized easily
CREATE_DATA = dict(
    name='AutoTask 4 Computer with notes priority 3',
    notes='Notes task 4',
    category=TaskCategory.Computer.value,
    priority=3,
    frequency=TaskFrequency.Biweekly.value,
)
