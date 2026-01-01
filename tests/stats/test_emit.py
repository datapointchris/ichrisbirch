"""Tests for event emission."""

from __future__ import annotations

import tempfile
from datetime import UTC
from datetime import datetime
from pathlib import Path


class TestEmitEvent:
    """Tests for emit_event function."""

    def test_emit_appends_to_jsonl(self) -> None:
        from stats.emit import emit_event
        from stats.schemas.base import BaseEvent

        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / 'events.jsonl'

            event = BaseEvent(
                timestamp=datetime.now(UTC),
                project='ichrisbirch',
                branch='master',
            )

            emit_event(event, str(events_path))

            assert events_path.exists()
            content = events_path.read_text()
            assert 'ichrisbirch' in content
            assert content.endswith('\n')

    def test_emit_creates_parent_directories(self) -> None:
        from stats.emit import emit_event
        from stats.schemas.base import BaseEvent

        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / 'nested' / 'dir' / 'events.jsonl'

            event = BaseEvent(
                timestamp=datetime.now(UTC),
                project='ichrisbirch',
                branch='master',
            )

            emit_event(event, str(events_path))

            assert events_path.exists()

    def test_emit_appends_multiple_events(self) -> None:
        from stats.emit import emit_event
        from stats.schemas.base import BaseEvent

        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / 'events.jsonl'

            for i in range(3):
                event = BaseEvent(
                    timestamp=datetime.now(UTC),
                    project='ichrisbirch',
                    branch=f'branch-{i}',
                )
                emit_event(event, str(events_path))

            lines = events_path.read_text().strip().split('\n')
            assert len(lines) == 3

    def test_emit_writes_valid_json(self) -> None:
        import json

        from stats.emit import emit_event
        from stats.schemas.base import BaseEvent

        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / 'events.jsonl'

            event = BaseEvent(
                timestamp=datetime.now(UTC),
                project='ichrisbirch',
                branch='master',
            )

            emit_event(event, str(events_path))

            content = events_path.read_text().strip()
            parsed = json.loads(content)
            assert parsed['project'] == 'ichrisbirch'
            assert parsed['branch'] == 'master'
