from datetime import datetime

from ichrisbirch.models import Event

BASE_DATA: list[Event] = [
    Event(
        name='Event 1',
        date=datetime(2022, 10, 1, 10, 0).isoformat(),
        venue='Venue 1',
        url='https://example.com/event1',
        cost=10.0,
        attending=True,
        notes='Notes for Event 1',
    ),
    Event(
        name='Event 2',
        date=datetime(2022, 10, 2, 14, 0).isoformat(),
        venue='Venue 2',
        url='https://example.com/event2',
        cost=20.0,
        attending=False,
        notes='Notes for Event 2',
    ),
    Event(
        name='Event 3',
        date=datetime(2022, 10, 3, 18, 0).isoformat(),
        venue='Venue 3',
        url='https://example.com/event3',
        cost=30.0,
        attending=True,
        notes='Notes for Event 3',
    ),
]
# dict so it can be JSON serialized easily
CREATE_DATA = dict(
    name='Event 4',
    date=datetime(2022, 10, 4, 20, 0).isoformat(),
    venue='Venue 4',
    url='https://example.com/event4',
    cost=40.0,
    attending=False,
    notes='Notes for Event 4',
)
