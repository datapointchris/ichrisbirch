from datetime import date

from ichrisbirch.models import Countdown

BASE_DATA: list[Countdown] = [
    Countdown(
        name='Countdown 1, get a raise',
        notes='Notes for Countdown 1',
        due_date=date(2020, 4, 24).isoformat(),
    ),
    Countdown(
        name='Countdown 2 Home without notes priority 10 not completed',
        notes=None,
        due_date=date(2050, 3, 20).isoformat(),
    ),
    Countdown(
        name='Countdown 3 Home with notes priority 15 completed',
        notes='Notes for Countdown 3',
        due_date=date(2050, 1, 20).isoformat(),
    ),
]
