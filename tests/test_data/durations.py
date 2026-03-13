from datetime import date

from ichrisbirch import models

BASE_DATA: list[models.Duration] = [
    models.Duration(
        name='Learning Piano',
        start_date=date(2023, 1, 15),
        end_date=None,
        notes='Self-taught with online courses',
        color='#4A90D9',
        duration_notes=[
            models.DurationNote(
                date=date(2023, 3, 1),
                content='Completed beginner course',
            ),
            models.DurationNote(
                date=date(2023, 9, 10),
                content='Started intermediate repertoire',
            ),
        ],
    ),
    models.Duration(
        name='Lived in North Carolina',
        start_date=date(2018, 6, 1),
        end_date=date(2022, 8, 15),
        notes='Raleigh area',
        color='#E74C3C',
        duration_notes=[
            models.DurationNote(
                date=date(2019, 1, 1),
                content='Got promoted at work',
            ),
        ],
    ),
    models.Duration(
        name='Running habit',
        start_date=date(2024, 4, 1),
        end_date=None,
        notes=None,
        color=None,
        duration_notes=[],
    ),
]
