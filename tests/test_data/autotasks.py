from datetime import datetime

from ichrisbirch.models import AutoTask

BASE_DATA: list[AutoTask] = [
    AutoTask(
        name='AutoTask 1 Chore with notes priority 5 not completed',
        notes='Notes for task 1',
        category='Chore',
        priority=5,
        frequency='Daily',
        first_run_date=datetime(2020, 4, 20, 3, 3, 39, 50648).isoformat(),
        last_run_date=datetime(2020, 4, 24, 3, 3, 39, 50648).isoformat(),
        run_count=5,
    ),
    AutoTask(
        name='AutoTask 2 Home without notes priority 10 not completed',
        notes=None,
        category='Home',
        priority=10,
        frequency='Weekly',
        first_run_date=datetime(2020, 3, 20, 3, 3, 39, 50648).isoformat(),
        last_run_date=datetime(2020, 3, 24, 3, 3, 39, 50648).isoformat(),
        run_count=1,
    ),
    AutoTask(
        name='AutoTask 3 Home with notes priority 15 completed',
        notes='Notes for task 3',
        category='Home',
        priority=15,
        frequency='Quarterly',
        first_run_date=datetime(2020, 1, 20, 3, 3, 39, 50648).isoformat(),
        last_run_date=datetime(2020, 1, 24, 3, 3, 39, 50648).isoformat(),
        run_count=2,
    ),
]
