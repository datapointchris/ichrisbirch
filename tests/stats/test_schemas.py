"""Tests for stats schemas."""

from __future__ import annotations

import datetime as dt

from stats.schemas.base import BaseEvent


class TestBaseEvent:
    """Tests for BaseEvent schema."""

    def test_base_event_has_required_fields(self) -> None:
        event = BaseEvent(
            timestamp=dt.datetime.now(dt.UTC),
            project='life',
            branch='master',
        )

        assert event.timestamp is not None
        assert event.project == 'life'
        assert event.branch == 'master'

    def test_base_event_serializes_to_json(self) -> None:
        event = BaseEvent(
            timestamp=dt.datetime(2025, 12, 31, 7, 36, 12, tzinfo=dt.UTC),
            project='life',
            branch='master',
        )

        json_str = event.model_dump_json()
        assert 'life' in json_str
        assert '2025-12-31' in json_str

    def test_base_event_deserializes_from_json(self) -> None:
        json_str = '{"timestamp": "2025-12-31T07:36:12Z", "project": "life", "branch": "master"}'
        event = BaseEvent.model_validate_json(json_str)

        assert event.project == 'life'
        assert event.branch == 'master'
