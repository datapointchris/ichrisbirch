"""Tests for event union and parsing."""

from __future__ import annotations

import json
import tempfile


class TestParseEvent:
    """Tests for parse_event function."""

    def test_parse_ruff_event(self) -> None:
        """Test parsing a ruff hook event."""
        from stats.schemas import parse_event
        from stats.schemas.hooks.ruff import RuffHookEvent

        data = {
            'type': 'hook.ruff',
            'timestamp': '2025-12-31T07:36:12Z',
            'project': 'ichrisbirch',
            'branch': 'master',
            'status': 'passed',
            'exit_code': 0,
            'issues': [],
            'files_checked': ['test.py'],
            'duration_seconds': 0.5,
        }
        json_line = json.dumps(data)

        event = parse_event(json_line)

        assert isinstance(event, RuffHookEvent)
        assert event.type == 'hook.ruff'
        assert event.status == 'passed'
        assert event.files_checked == ['test.py']

    def test_parse_mypy_event(self) -> None:
        """Test parsing a mypy hook event."""
        from stats.schemas import parse_event
        from stats.schemas.hooks.mypy import MypyHookEvent

        data = {
            'type': 'hook.mypy',
            'timestamp': '2025-12-31T07:36:12Z',
            'project': 'ichrisbirch',
            'branch': 'master',
            'status': 'passed',
            'exit_code': 0,
            'errors': [],
            'files_checked': ['test.py'],
            'duration_seconds': 0.3,
        }
        json_line = json.dumps(data)

        event = parse_event(json_line)

        assert isinstance(event, MypyHookEvent)
        assert event.type == 'hook.mypy'

    def test_parse_commit_event(self) -> None:
        """Test parsing a commit event."""
        from stats.schemas import parse_event
        from stats.schemas.commit import CommitEvent

        data = {
            'type': 'commit',
            'timestamp': '2025-12-31T07:37:00Z',
            'project': 'ichrisbirch',
            'branch': 'master',
            'hash': 'abc123',
            'short_hash': 'abc',
            'message': 'test commit',
            'author': 'Test',
            'email': 'test@test.com',
            'files_changed': 1,
            'insertions': 10,
            'deletions': 5,
            'staged_files': [],
        }
        json_line = json.dumps(data)

        event = parse_event(json_line)

        assert isinstance(event, CommitEvent)
        assert event.type == 'commit'
        assert event.hash == 'abc123'

    def test_parse_tokei_event(self) -> None:
        """Test parsing a tokei collect event."""
        from stats.schemas import parse_event
        from stats.schemas.collectors.tokei import TokeiCollectEvent

        data = {
            'type': 'collect.tokei',
            'timestamp': '2025-12-31T07:36:12Z',
            'project': 'ichrisbirch',
            'branch': 'master',
            'total_files': 100,
            'total_code': 8000,
            'total_comments': 1000,
            'total_blanks': 1000,
            'languages': {},
            'duration_seconds': 0.5,
        }
        json_line = json.dumps(data)

        event = parse_event(json_line)

        assert isinstance(event, TokeiCollectEvent)
        assert event.type == 'collect.tokei'

    def test_parse_bandit_event(self) -> None:
        """Test parsing a bandit hook event."""
        from stats.schemas import parse_event
        from stats.schemas.hooks.bandit import BanditHookEvent

        data = {
            'type': 'hook.bandit',
            'timestamp': '2025-12-31T07:36:12Z',
            'project': 'ichrisbirch',
            'branch': 'master',
            'status': 'passed',
            'exit_code': 0,
            'issues': [],
            'files_checked': [],
            'metrics': {
                'skipped_tests': 0,
                'loc': 1000,
                'nosec': 0,
                'confidence': {'high': 0, 'low': 0, 'medium': 0, 'undefined': 0},
                'severity': {'high': 0, 'low': 0, 'medium': 0, 'undefined': 0},
            },
            'duration_seconds': 0.3,
        }
        json_line = json.dumps(data)

        event = parse_event(json_line)

        assert isinstance(event, BanditHookEvent)
        assert event.type == 'hook.bandit'


class TestParseEventsFile:
    """Tests for parse_events_file function."""

    def test_parse_events_file_multiple_events(self) -> None:
        """Test parsing multiple events from a JSONL file."""
        from stats.schemas import parse_events_file
        from stats.schemas.commit import CommitEvent
        from stats.schemas.hooks.ruff import RuffHookEvent

        ruff_event = {
            'type': 'hook.ruff',
            'timestamp': '2025-12-31T07:35:00Z',
            'project': 'ichrisbirch',
            'branch': 'master',
            'status': 'passed',
            'exit_code': 0,
            'issues': [],
            'files_checked': [],
            'duration_seconds': 0.5,
        }
        commit_event = {
            'type': 'commit',
            'timestamp': '2025-12-31T07:37:00Z',
            'project': 'ichrisbirch',
            'branch': 'master',
            'hash': 'abc123',
            'short_hash': 'abc',
            'message': 'test',
            'author': 'Test',
            'email': 'test@test.com',
            'files_changed': 1,
            'insertions': 10,
            'deletions': 5,
            'staged_files': [],
        }
        jsonl_content = json.dumps(ruff_event) + '\n' + json.dumps(commit_event)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write(jsonl_content)
            f.flush()

            events = parse_events_file(f.name)

            assert len(events) == 2
            assert isinstance(events[0], RuffHookEvent)
            assert isinstance(events[1], CommitEvent)

    def test_parse_events_file_empty(self) -> None:
        """Test parsing an empty file."""
        from stats.schemas import parse_events_file

        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('')
            f.flush()

            events = parse_events_file(f.name)

            assert not events

    def test_parse_events_file_nonexistent(self) -> None:
        """Test parsing a non-existent file."""
        from stats.schemas import parse_events_file

        events = parse_events_file('/nonexistent/file.jsonl')

        assert not events


class TestEventTypes:
    """Tests for the Event union type."""

    def test_all_hook_types_in_union(self) -> None:
        """Test that all hook types are in the Event union."""
        from stats.schemas import Event
        from stats.schemas.hooks.bandit import BanditHookEvent
        from stats.schemas.hooks.codespell import CodespellHookEvent
        from stats.schemas.hooks.mypy import MypyHookEvent
        from stats.schemas.hooks.ruff import RuffHookEvent
        from stats.schemas.hooks.shellcheck import ShellcheckHookEvent

        hook_types = [
            RuffHookEvent,
            MypyHookEvent,
            BanditHookEvent,
            ShellcheckHookEvent,
            CodespellHookEvent,
        ]

        union_types = list(Event.__args__)

        for hook_type in hook_types:
            assert hook_type in union_types, f'{hook_type.__name__} not in Event union'

    def test_all_collector_types_in_union(self) -> None:
        """Test that all collector types are in the Event union."""
        from stats.schemas import Event
        from stats.schemas.collectors.coverage import CoverageCollectEvent
        from stats.schemas.collectors.dependencies import DependenciesCollectEvent
        from stats.schemas.collectors.docker import DockerCollectEvent
        from stats.schemas.collectors.files import FilesCollectEvent
        from stats.schemas.collectors.pytest_collector import PytestCollectEvent
        from stats.schemas.collectors.tokei import TokeiCollectEvent

        collector_types = [
            TokeiCollectEvent,
            PytestCollectEvent,
            CoverageCollectEvent,
            DockerCollectEvent,
            DependenciesCollectEvent,
            FilesCollectEvent,
        ]

        union_types = list(Event.__args__)

        for collector_type in collector_types:
            assert collector_type in union_types, f'{collector_type.__name__} not in Event union'

    def test_commit_type_in_union(self) -> None:
        """Test that CommitEvent is in the Event union."""
        from stats.schemas import Event
        from stats.schemas.commit import CommitEvent

        union_types = list(Event.__args__)

        assert CommitEvent in union_types


class TestTokeiSchema:
    """Test that TokeiCollectEvent schema has the right fields."""

    def test_tokei_total_lines_optional(self) -> None:
        """Test TokeiCollectEvent can be created without total_lines."""
        from datetime import UTC
        from datetime import datetime

        from stats.schemas.collectors.tokei import TokeiCollectEvent

        event = TokeiCollectEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            total_files=100,
            total_code=8000,
            total_comments=1000,
            total_blanks=1000,
            languages={},
            duration_seconds=0.5,
        )

        assert event.total_files == 100
