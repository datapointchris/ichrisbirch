"""Tests for stats schemas."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime


class TestBaseEvent:
    """Tests for BaseEvent schema."""

    def test_base_event_has_required_fields(self) -> None:
        from stats.schemas.base import BaseEvent

        event = BaseEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
        )

        assert event.timestamp is not None
        assert event.project == 'ichrisbirch'
        assert event.branch == 'master'

    def test_base_event_serializes_to_json(self) -> None:
        from stats.schemas.base import BaseEvent

        event = BaseEvent(
            timestamp=datetime(2025, 12, 31, 7, 36, 12, tzinfo=UTC),
            project='ichrisbirch',
            branch='master',
        )

        json_str = event.model_dump_json()
        assert 'ichrisbirch' in json_str
        assert '2025-12-31' in json_str

    def test_base_event_deserializes_from_json(self) -> None:
        from stats.schemas.base import BaseEvent

        json_str = '{"timestamp": "2025-12-31T07:36:12Z", "project": "ichrisbirch", "branch": "master"}'
        event = BaseEvent.model_validate_json(json_str)

        assert event.project == 'ichrisbirch'
        assert event.branch == 'master'
