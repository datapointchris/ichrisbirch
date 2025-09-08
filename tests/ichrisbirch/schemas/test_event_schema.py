"""Tests for the event schema validation.

Tests that the Event, EventCreate, and EventUpdate schemas properly validate data.
"""

import datetime

import pendulum
import pytest
from pydantic import ValidationError

from ichrisbirch.schemas.event import Event
from ichrisbirch.schemas.event import EventCreate
from ichrisbirch.schemas.event import EventUpdate


class TestEventSchema:
    def test_event_create_valid(self):
        """Test creating a valid EventCreate model."""
        event_data = {
            'name': 'Concert',
            'date': datetime.datetime(2023, 6, 15, 20, 0, 0),
            'venue': 'Stadium',
            'url': 'https://example.com/concert',
            'cost': 75.50,
            'attending': True,
            'notes': 'Front row seats',
        }
        event = EventCreate(**event_data)
        assert event.name == 'Concert'
        assert isinstance(event.date, datetime.datetime)
        assert event.venue == 'Stadium'
        assert event.url == 'https://example.com/concert'
        assert event.cost == 75.50
        assert event.attending is True
        assert event.notes == 'Front row seats'

    def test_event_create_minimum_required(self):
        """Test creating an event with only required fields."""
        event_data = {
            'name': 'Concert',
            'date': datetime.datetime(2023, 6, 15, 20, 0, 0),
            'venue': 'Stadium',
            'cost': 75.50,
            'attending': False,
        }
        event = EventCreate(**event_data)
        assert event.name == 'Concert'
        assert event.url is None
        assert event.attending is False
        assert event.notes is None

    def test_event_create_with_string_date(self):
        """Test creating an event with a string date that gets converted."""
        event_data = {'name': 'Concert', 'date': '2023-06-15T20:00:00', 'venue': 'Stadium', 'cost': 75.50, 'attending': True}
        event = EventCreate(**event_data)
        assert isinstance(event.date, datetime.datetime)
        assert event.date.year == 2023
        assert event.date.month == 6
        assert event.date.day == 15

    def test_event_create_with_timezone_string(self):
        """Test creating an event with a timezone string that gets converted."""
        event_data = {'name': 'Concert', 'date': '2023-06-15T20:00:00-05:00', 'venue': 'Stadium', 'cost': 75.50, 'attending': True}
        event = EventCreate(**event_data)
        # Should be converted to UTC
        dt = pendulum.instance(event.date)
        assert dt.timezone_name == 'UTC'
        # Original was 20:00 -05:00, which is 01:00 UTC next day
        assert dt.hour == 1
        assert dt.day == 16  # Next day in UTC

    def test_event_create_invalid_missing_fields(self):
        """Test EventCreate fails with missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            EventCreate(name='Concert', venue='Stadium', attending=True)

        errors = exc_info.value.errors()
        assert any(err['type'] == 'missing' and err['loc'][0] in ('date', 'cost') for err in errors)

    def test_event_create_invalid_date(self):
        """Test EventCreate fails with invalid date format."""
        with pytest.raises(ValidationError):
            EventCreate(name='Concert', date='invalid-date', venue='Stadium', cost=75.50, attending=True)

    def test_event_model_valid(self):
        """Test creating a valid Event model."""
        now = datetime.datetime.now()
        event_data = {
            'id': 1,
            'name': 'Concert',
            'date': now,
            'venue': 'Stadium',
            'url': 'https://example.com/concert',
            'cost': 75.50,
            'attending': True,
            'notes': 'Front row seats',
        }
        event = Event(**event_data)
        assert event.id == 1
        assert event.name == 'Concert'
        assert event.date == now
        assert event.venue == 'Stadium'
        assert event.url == 'https://example.com/concert'
        assert event.cost == 75.50
        assert event.attending is True
        assert event.notes == 'Front row seats'

    def test_event_model_missing_fields(self):
        """Test Event model fails with missing required fields."""
        incomplete_data = {'name': 'Concert', 'venue': 'Stadium', 'cost': 75.50, 'attending': True}

        with pytest.raises(ValidationError):
            Event(**incomplete_data)

    def test_event_update_valid(self):
        """Test creating a valid EventUpdate model."""
        event_update = EventUpdate(name='Updated Concert', attending=False)
        assert event_update.name == 'Updated Concert'
        assert event_update.attending is False
        assert event_update.date is None
        assert event_update.venue is None
        assert event_update.url is None
        assert event_update.cost is None
        assert event_update.notes is None

    def test_event_update_empty(self):
        """Test creating an empty EventUpdate is valid (all fields optional)."""
        event_update = EventUpdate()
        assert event_update.name is None
        assert event_update.date is None
        assert event_update.venue is None
        assert event_update.url is None
        assert event_update.cost is None
        assert event_update.attending is None
        assert event_update.notes is None
