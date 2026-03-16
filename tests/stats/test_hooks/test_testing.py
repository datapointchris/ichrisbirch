"""Tests for pre-commit test gate hooks (pytest-affected, pytest-full)."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from unittest.mock import MagicMock
from unittest.mock import patch


class TestPytestAffectedSchema:
    """Tests for PytestAffectedHookEvent schema."""

    def test_pytest_affected_hook_event_passed(self) -> None:
        from stats.schemas.hooks.testing import PytestAffectedHookEvent

        event = PytestAffectedHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            tests_selected=12,
            duration_seconds=5.2,
        )

        assert event.type == 'hook.pytest-affected'
        assert event.status == 'passed'
        assert event.tests_selected == 12

    def test_pytest_affected_hook_event_skipped(self) -> None:
        from stats.schemas.hooks.testing import PytestAffectedHookEvent

        event = PytestAffectedHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='skipped',
            exit_code=0,
            tests_selected=0,
            duration_seconds=0.0,
        )

        assert event.status == 'skipped'
        assert event.tests_selected == 0

    def test_pytest_affected_hook_event_failed(self) -> None:
        """Test PytestAffectedHookEvent with failing tests."""
        from stats.schemas.hooks.testing import PytestAffectedHookEvent

        event = PytestAffectedHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            tests_selected=3,
            duration_seconds=1.5,
        )

        assert event.type == 'hook.pytest-affected'
        assert event.status == 'failed'
        assert event.tests_selected == 3


class TestPytestAffectedRunner:
    """Tests for pytest-affected hook runner."""

    def test_pytest_affected_runner_skips_no_python(self) -> None:
        from stats.hooks.pytest_affected import run

        event = run(['README.md', 'style.css'], 'master', 'ichrisbirch')

        assert event.status == 'skipped'
        assert event.tests_selected == 0

    def test_pytest_affected_runner_parses_output(self) -> None:
        from stats.hooks.pytest_affected import run
        from stats.schemas.hooks.testing import PytestAffectedHookEvent

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='===== 5 passed in 2.34s =====',
                stderr='',
            )

            event = run(['main.py'], 'master', 'ichrisbirch')

            assert isinstance(event, PytestAffectedHookEvent)
            assert event.status == 'passed'
            assert event.tests_selected == 5

    def test_pytest_affected_runner_handles_failure(self) -> None:
        from stats.hooks.pytest_affected import run

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout='FAILED tests/test_main.py::test_x - AssertionError\n===== 1 failed, 4 passed in 3.12s =====',
                stderr='',
            )

            event = run(['main.py'], 'master', 'ichrisbirch')

            assert event.status == 'failed'

    def test_pytest_affected_runner_measures_duration(self) -> None:
        """Test runner measures execution duration."""
        from stats.hooks.pytest_affected import run

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='===== 3 passed in 1.50s =====',
                stderr='',
            )

            event = run(['ichrisbirch/api/main.py'], 'master', 'ichrisbirch')

            assert event.duration_seconds >= 0


class TestPytestFullSchema:
    """Tests for PytestFullHookEvent schema."""

    def test_pytest_full_hook_event(self) -> None:
        from stats.schemas.hooks.testing import PytestFullHookEvent

        event = PytestFullHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            tests_run=150,
            duration_seconds=45.0,
        )

        assert event.type == 'hook.pytest-full'
        assert event.tests_run == 150

    def test_pytest_full_hook_event_failed(self) -> None:
        """Test PytestFullHookEvent with failing tests."""
        from stats.schemas.hooks.testing import PytestFullHookEvent

        event = PytestFullHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            tests_run=42,
            duration_seconds=15.7,
        )

        assert event.type == 'hook.pytest-full'
        assert event.status == 'failed'

    def test_pytest_full_hook_event_skipped(self) -> None:
        """Test PytestFullHookEvent with skipped status."""
        from stats.schemas.hooks.testing import PytestFullHookEvent

        event = PytestFullHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='skipped',
            exit_code=0,
            tests_run=0,
            duration_seconds=0.0,
        )

        assert event.type == 'hook.pytest-full'
        assert event.status == 'skipped'
        assert event.tests_run == 0


class TestPytestFullRunner:
    """Tests for pytest-full hook runner."""

    def test_pytest_full_runner_skips_no_python(self) -> None:
        from stats.hooks.pytest_full import run
        from stats.schemas.hooks.testing import PytestFullHookEvent

        events = run(['README.md'], 'master', 'ichrisbirch')

        assert len(events) == 1
        assert isinstance(events[0], PytestFullHookEvent)
        assert events[0].status == 'skipped'
        assert events[0].tests_run == 0

    def test_pytest_full_runner_parses_output(self) -> None:
        from stats.hooks.pytest_full import run
        from stats.schemas.hooks.testing import PytestFullHookEvent

        with (
            patch('stats.hooks.pytest_full.subprocess.run') as mock_run,
            patch('stats.hooks.pytest_full.pytest_collector.run', return_value=None),
        ):
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='===== 150 passed in 45.12s =====',
                stderr='',
            )

            events = run(['main.py'], 'master', 'ichrisbirch')

            assert len(events) == 1
            hook_event = events[0]
            assert isinstance(hook_event, PytestFullHookEvent)
            assert hook_event.status == 'passed'
            assert hook_event.tests_run == 150

    def test_pytest_full_runner_emits_collect_event(self) -> None:
        """Test runner emits both hook and collector events when JSON report exists."""
        from stats.hooks.pytest_full import run
        from stats.schemas.collectors.pytest_collector import PytestCollectEvent
        from stats.schemas.collectors.pytest_collector import PytestSummary
        from stats.schemas.hooks.testing import PytestFullHookEvent

        mock_collect_event = PytestCollectEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            summary=PytestSummary(passed=148, failed=2, total=150),
            tests=[],
            duration_seconds=45.0,
            exit_code=1,
        )

        with (
            patch('stats.hooks.pytest_full.subprocess.run') as mock_run,
            patch('stats.hooks.pytest_full.pytest_collector.run', return_value=mock_collect_event),
        ):
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout='===== 2 failed, 148 passed in 45.12s =====',
                stderr='',
            )

            events = run(['main.py'], 'master', 'ichrisbirch')

            assert len(events) == 2
            assert isinstance(events[0], PytestFullHookEvent)
            assert isinstance(events[1], PytestCollectEvent)
            assert events[0].status == 'failed'
            assert events[1].summary.failed == 2

    def test_pytest_full_runner_handles_failure(self) -> None:
        """Test runner returns failed event for failing tests."""
        from stats.hooks.pytest_full import run
        from stats.schemas.hooks.testing import PytestFullHookEvent

        with (
            patch('stats.hooks.pytest_full.subprocess.run') as mock_run,
            patch('stats.hooks.pytest_full.pytest_collector.run', return_value=None),
        ):
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout='===== 2 failed, 40 passed in 16.30s =====',
                stderr='',
            )

            events = run(['ichrisbirch/api/main.py'], 'master', 'ichrisbirch')

            hook_event = events[0]
            assert isinstance(hook_event, PytestFullHookEvent)
            assert hook_event.status == 'failed'
            assert hook_event.exit_code == 1

    def test_pytest_full_runner_measures_duration(self) -> None:
        """Test runner measures execution duration."""
        from stats.hooks.pytest_full import run

        with (
            patch('stats.hooks.pytest_full.subprocess.run') as mock_run,
            patch('stats.hooks.pytest_full.pytest_collector.run', return_value=None),
        ):
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='===== 42 passed in 15.70s =====',
                stderr='',
            )

            events = run(['ichrisbirch/api/main.py'], 'master', 'ichrisbirch')

            assert events[0].duration_seconds >= 0
