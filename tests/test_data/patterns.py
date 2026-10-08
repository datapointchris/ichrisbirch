import datetime as dt

from ichrisbirch.models import Pattern

BASE_DATA: list[Pattern] = [
    Pattern(
        message='Pattern 1, coffee at 3pm and awake until midnight',
        recorded_at=dt.datetime(2026, 1, 5, 15, 0, tzinfo=dt.UTC),
    ),
    Pattern(
        message='Pattern 2, heartburn after soy sauce',
        recorded_at=dt.datetime(2026, 1, 6, 19, 30, tzinfo=dt.UTC),
    ),
    Pattern(
        message='Pattern 3, walked after dinner and slept through',
        recorded_at=dt.datetime(2026, 1, 7, 21, 15, tzinfo=dt.UTC),
    ),
]
