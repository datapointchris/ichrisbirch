"""Tests for ruff hook schema and runner."""

from __future__ import annotations

import json
from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


class TestRuffSchema:
    """Tests for RuffHookEvent schema."""

    def test_ruff_issue_schema_parses_real_output(self) -> None:
        """Test that RuffIssue can parse real ruff output."""
        from stats.schemas.hooks.ruff import RuffIssue

        issues = json.loads((FIXTURES_DIR / 'ruff_with_issues.json').read_text())

        if not issues:
            pytest.skip('No issues in fixture')

        issue = RuffIssue.model_validate(issues[0])

        assert issue.code == 'SIM105'
        assert issue.message is not None
        assert issue.filename is not None
        assert issue.location.row > 0
        assert issue.fix is not None
        assert issue.fix.applicability == 'unsafe'

    def test_ruff_hook_event_with_issues(self) -> None:
        """Test RuffHookEvent with issues."""
        from stats.schemas.hooks.ruff import RuffHookEvent
        from stats.schemas.hooks.ruff import RuffIssue

        issues = json.loads((FIXTURES_DIR / 'ruff_with_issues.json').read_text())
        parsed_issues = [RuffIssue.model_validate(i) for i in issues]

        event = RuffHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            issues=parsed_issues,
            files_checked=['test.py'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.ruff'
        assert event.status == 'failed'
        assert len(event.issues) == 2

    def test_ruff_hook_event_clean(self) -> None:
        """Test RuffHookEvent with no issues."""
        from stats.schemas.hooks.ruff import RuffHookEvent

        event = RuffHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            issues=[],
            files_checked=['test.py'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.ruff'
        assert event.status == 'passed'
        assert not event.issues

    def test_ruff_hook_event_serializes_to_json(self) -> None:
        """Test RuffHookEvent can be serialized to JSON."""
        from stats.schemas.hooks.ruff import RuffHookEvent

        event = RuffHookEvent(
            timestamp=datetime(2025, 12, 31, 7, 36, 12, tzinfo=UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            issues=[],
            files_checked=['test.py'],
            duration_seconds=0.5,
        )

        json_str = event.model_dump_json()
        assert '"type":"hook.ruff"' in json_str
        assert '"status":"passed"' in json_str


class TestRuffRunner:
    """Tests for ruff hook runner."""

    def test_ruff_runner_returns_typed_event_clean(self) -> None:
        """Test runner returns RuffHookEvent for clean output."""
        from stats.hooks.ruff import run
        from stats.schemas.hooks.ruff import RuffHookEvent

        clean_output = (FIXTURES_DIR / 'ruff_clean.json').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=clean_output,
                stderr='',
            )

            event = run(['test.py'], 'master', 'ichrisbirch')

            assert isinstance(event, RuffHookEvent)
            assert event.status == 'passed'
            assert event.exit_code == 0
            assert not event.issues

    def test_ruff_runner_parses_issues(self) -> None:
        """Test runner parses issues from ruff output."""
        from stats.hooks.ruff import run
        from stats.schemas.hooks.ruff import RuffHookEvent

        issues_output = (FIXTURES_DIR / 'ruff_with_issues.json').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=issues_output,
                stderr='',
            )

            event = run(['test.py'], 'master', 'ichrisbirch')

            assert isinstance(event, RuffHookEvent)
            assert event.status == 'failed'
            assert len(event.issues) == 2
            assert event.issues[0].code == 'SIM105'

    def test_ruff_runner_measures_duration(self) -> None:
        """Test runner measures execution duration."""
        from stats.hooks.ruff import run

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='[]',
                stderr='',
            )

            event = run(['test.py'], 'master', 'ichrisbirch')

            assert event.duration_seconds >= 0
