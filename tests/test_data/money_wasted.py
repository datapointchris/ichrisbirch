from datetime import date

from ichrisbirch.models import MoneyWasted

BASE_DATA: list[MoneyWasted] = [
    MoneyWasted(
        item='MoneyWasted 1, Purchase and Waste Date',
        amount=10.0,
        date_purchased=date(2020, 4, 24).isoformat(),
        date_wasted=date(2020, 4, 24).isoformat(),
        notes='Notes for MoneyWasted 1',
    ),
    MoneyWasted(
        item='MoneyWasted 2 No Purchase Date',
        amount=20.0,
        date_wasted=date(2050, 3, 20).isoformat(),
        notes=None,
    ),
    MoneyWasted(
        item='MoneyWasted Big 3',
        amount=300_000.0,
        date_purchased=date(2050, 1, 20).isoformat(),
        date_wasted=date(2050, 1, 20).isoformat(),
        notes='Should not have bought that house lol',
    ),
]
