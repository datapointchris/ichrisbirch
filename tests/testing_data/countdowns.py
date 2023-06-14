from datetime import date

from ichrisbirch.models.countdown import Countdown

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
# dict so it can be JSON serialized easily
CREATE_DATA = dict(
    name='Countdown 4 Computer with notes priority 3',
    notes='Notes Countdown 4',
    due_date=date(2040, 1, 20).isoformat(),
)
