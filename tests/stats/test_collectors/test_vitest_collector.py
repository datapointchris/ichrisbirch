"""Tests for vitest collector schema and runner."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


class TestVitestSchema:
    """Tests for VitestCollectEvent schema."""

    def test_vitest_summary_schema(self) -> None:
        """Test that VitestSummary captures all fields."""
        from stats.schemas.collectors.vitest_collector import VitestSummary

        summary = VitestSummary(
            passed=4,
            failed=1,
            skipped=0,
            total=5,
        )

        assert summary.passed == 4
        assert summary.failed == 1
        assert summary.skipped == 0
        assert summary.total == 5

    def test_vitest_test_schema(self) -> None:
        """Test that VitestTest captures all fields."""
        from stats.schemas.collectors.vitest_collector import VitestTest

        test = VitestTest(
            name='BookStore > should load books',
            suite='/frontend/src/stores/__tests__/books.test.ts',
            outcome='passed',
            duration=0.045,
        )

        assert test.name == 'BookStore > should load books'
        assert test.suite == '/frontend/src/stores/__tests__/books.test.ts'
        assert test.outcome == 'passed'
        assert test.duration == 0.045

    def test_vitest_collect_event_schema(self) -> None:
        """Test VitestCollectEvent schema."""
        from stats.schemas.collectors.vitest_collector import VitestCollectEvent
        from stats.schemas.collectors.vitest_collector import VitestSummary

        event = VitestCollectEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            summary=VitestSummary(passed=4, failed=1, total=5),
            tests=[],
            duration_seconds=0.203,
            exit_code=1,
        )

        assert event.type == 'collect.vitest'
        assert event.summary.passed == 4
        assert event.summary.failed == 1
        assert event.exit_code == 1


class TestVitestRunner:
    """Tests for vitest collector runner."""

    def test_vitest_runner_returns_none_for_missing_file(self) -> None:
        """Test runner returns None if file doesn't exist."""
        from stats.collectors.vitest_collector import run

        event = run('master', 'ichrisbirch', '/nonexistent/path.json')

        assert event is None

    def test_vitest_runner_returns_typed_event(self) -> None:
        """Test runner returns VitestCollectEvent."""
        from stats.collectors.vitest_collector import run
        from stats.schemas.collectors.vitest_collector import VitestCollectEvent

        json_path = FIXTURES_DIR / 'vitest_report.json'
        event = run('master', 'ichrisbirch', str(json_path))

        assert event is not None
        assert isinstance(event, VitestCollectEvent)
        assert event.summary.total == 5
        assert event.summary.passed == 4
        assert event.summary.failed == 1
        assert event.summary.skipped == 0

    def test_vitest_runner_parses_tests(self) -> None:
        """Test runner parses and flattens test details."""
        from stats.collectors.vitest_collector import run

        json_path = FIXTURES_DIR / 'vitest_report.json'
        event = run('master', 'ichrisbirch', str(json_path))

        assert event is not None
        assert len(event.tests) == 5

        # Durations should be converted from ms to seconds
        books_load = next(t for t in event.tests if 'should load books' in t.name)
        assert books_load.duration == 0.045

        books_update = next(t for t in event.tests if 'should update book' in t.name)
        assert books_update.duration == 0.089
        assert books_update.outcome == 'failed'

    def test_vitest_runner_sets_exit_code(self) -> None:
        """Test runner sets exit_code based on success field."""
        from stats.collectors.vitest_collector import run

        json_path = FIXTURES_DIR / 'vitest_report.json'
        event = run('master', 'ichrisbirch', str(json_path))

        assert event is not None
        # Fixture has "success": false
        assert event.exit_code == 1
