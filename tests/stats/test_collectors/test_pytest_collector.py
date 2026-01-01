"""Tests for pytest collector schema and runner."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


class TestPytestSchema:
    """Tests for PytestCollectEvent schema."""

    def test_pytest_summary_schema(self) -> None:
        """Test that PytestSummary captures all fields."""
        from stats.schemas.collectors.pytest_collector import PytestSummary

        summary = PytestSummary(
            passed=100,
            failed=5,
            skipped=2,
            error=1,
            total=108,
            collected=108,
        )

        assert summary.passed == 100
        assert summary.failed == 5
        assert summary.total == 108

    def test_pytest_test_schema(self) -> None:
        """Test that PytestTest captures all fields."""
        from stats.schemas.collectors.pytest_collector import PytestPhase
        from stats.schemas.collectors.pytest_collector import PytestTest

        test = PytestTest(
            nodeid='tests/test_foo.py::test_bar',
            outcome='passed',
            duration=0.5,
            call=PytestPhase(outcome='passed', duration=0.4),
        )

        assert test.nodeid == 'tests/test_foo.py::test_bar'
        assert test.outcome == 'passed'
        assert test.call is not None

    def test_pytest_collect_event_schema(self) -> None:
        """Test PytestCollectEvent schema."""
        from stats.schemas.collectors.pytest_collector import PytestCollectEvent
        from stats.schemas.collectors.pytest_collector import PytestSummary

        event = PytestCollectEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            summary=PytestSummary(passed=100, total=100),
            tests=[],
            duration_seconds=10.5,
            exit_code=0,
        )

        assert event.type == 'collect.pytest'
        assert event.summary.passed == 100


class TestPytestRunner:
    """Tests for pytest collector runner."""

    def test_pytest_runner_returns_typed_event(self) -> None:
        """Test runner returns PytestCollectEvent."""
        from stats.collectors.pytest_collector import run
        from stats.schemas.collectors.pytest_collector import PytestCollectEvent

        json_path = FIXTURES_DIR / 'pytest_report.json'
        event = run('master', 'ichrisbirch', str(json_path))

        assert event is not None
        assert isinstance(event, PytestCollectEvent)
        assert event.summary.passed == 548

    def test_pytest_runner_parses_tests(self) -> None:
        """Test runner parses test details."""
        from stats.collectors.pytest_collector import run

        json_path = FIXTURES_DIR / 'pytest_report.json'
        event = run('master', 'ichrisbirch', str(json_path))

        assert event is not None
        assert len(event.tests) == 4
        assert event.tests[0].outcome == 'passed'

    def test_pytest_runner_returns_none_for_missing_file(self) -> None:
        """Test runner returns None if file doesn't exist."""
        from stats.collectors.pytest_collector import run

        event = run('master', 'ichrisbirch', '/nonexistent/path.json')

        assert event is None

    def test_pytest_runner_parses_failed_tests(self) -> None:
        """Test runner parses failed test details."""
        from stats.collectors.pytest_collector import run

        json_path = FIXTURES_DIR / 'pytest_report.json'
        event = run('master', 'ichrisbirch', str(json_path))

        assert event is not None
        failed_tests = [t for t in event.tests if t.outcome == 'failed']
        assert len(failed_tests) == 1
        assert failed_tests[0].call is not None
        assert failed_tests[0].call.longrepr is not None
