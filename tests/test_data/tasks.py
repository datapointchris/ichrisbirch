from datetime import UTC
from datetime import datetime

from ichrisbirch.models.task import Task

BASE_DATA: list[Task] = [
    Task(
        name='Task 1 Chore with notes ranked first not completed',
        notes='Notes for task 1',
        category='Chore',
        window_days=30,
        add_date=datetime(2020, 4, 1, 12, tzinfo=UTC),
        rank_at=datetime(2020, 5, 1, 12, tzinfo=UTC),
    ),
    Task(
        name='Task 2 Home without notes ranked second not completed',
        notes=None,
        category='Home',
        window_days=60,
        add_date=datetime(2020, 4, 1, 12, tzinfo=UTC),
        rank_at=datetime(2020, 5, 31, 12, tzinfo=UTC),
    ),
    Task(
        name='Task 3 Home with notes ranked third completed',
        notes='Notes for task 3',
        category='Home',
        window_days=60,
        add_date=datetime(2020, 4, 1, 12, tzinfo=UTC),
        rank_at=datetime(2020, 5, 31, 13, tzinfo=UTC),
        complete_date=datetime(2020, 4, 20, 3, 3, 39, 50648, tzinfo=UTC),
    ),
]
