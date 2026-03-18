"""Tests for ruff hook schema and runner."""

from __future__ import annotations

import json
from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from stats.hooks.ruff_check import run as ruff_check_run
from stats.hooks.ruff_format import run as ruff_format_run
from stats.schemas.hooks.ruff_check import RuffCheckHookEvent
from stats.schemas.hooks.ruff_check import RuffFormatHookEvent
from stats.schemas.hooks.ruff_check import RuffIssue

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


class TestRuffSchema:
    """Tests for RuffCheckHookEvent schema."""

    def test_ruff_issue_schema_parses_real_output(self) -> None:
        """Test that RuffIssue can parse real ruff output."""
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
        """Test RuffCheckHookEvent with issues."""
        issues = json.loads((FIXTURES_DIR / 'ruff_with_issues.json').read_text())
        parsed_issues = [RuffIssue.model_validate(i) for i in issues]

        event = RuffCheckHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            issues=parsed_issues,
            files_checked=['test.py'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.ruff-check'
        assert event.status == 'failed'
        assert len(event.issues) == 2

    def test_ruff_hook_event_clean(self) -> None:
        """Test RuffCheckHookEvent with no issues."""
        event = RuffCheckHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            issues=[],
            files_checked=['test.py'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.ruff-check'
        assert event.status == 'passed'
        assert not event.issues

    def test_ruff_hook_event_serializes_to_json(self) -> None:
        """Test RuffCheckHookEvent can be serialized to JSON."""
        event = RuffCheckHookEvent(
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
        assert '"type":"hook.ruff-check"' in json_str
        assert '"status":"passed"' in json_str


class TestRuffRunner:
    """Tests for ruff hook runner."""

    def test_ruff_runner_returns_typed_event_clean(self) -> None:
        """Test runner returns RuffCheckHookEvent for clean output."""
        clean_output = (FIXTURES_DIR / 'ruff_clean.json').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=clean_output,
                stderr='',
            )

            event = ruff_check_run(['test.py'], 'master', 'ichrisbirch')

            assert isinstance(event, RuffCheckHookEvent)
            assert event.status == 'passed'
            assert event.exit_code == 0
            assert not event.issues

    def test_ruff_runner_parses_issues(self) -> None:
        """Test runner parses issues from ruff output."""
        issues_output = (FIXTURES_DIR / 'ruff_with_issues.json').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=issues_output,
                stderr='',
            )

            event = ruff_check_run(['test.py'], 'master', 'ichrisbirch')

            assert isinstance(event, RuffCheckHookEvent)
            assert event.status == 'failed'
            assert len(event.issues) == 2
            assert event.issues[0].code == 'SIM105'

    def test_ruff_runner_measures_duration(self) -> None:
        """Test runner measures execution duration."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='[]',
                stderr='',
            )

            event = ruff_check_run(['test.py'], 'master', 'ichrisbirch')

            assert event.duration_seconds >= 0


class TestRuffFormatSchema:
    """Tests for RuffFormatHookEvent schema."""

    def test_ruff_format_hook_event_with_changes(self) -> None:
        """Test RuffFormatHookEvent with files needing reformatting."""
        event = RuffFormatHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            files_reformatted=['ichrisbirch/api/main.py', 'ichrisbirch/models/book.py'],
            files_checked=['ichrisbirch/api/main.py', 'ichrisbirch/models/book.py'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.ruff-format'
        assert event.status == 'failed'
        assert len(event.files_reformatted) == 2

    def test_ruff_format_hook_event_clean(self) -> None:
        """Test RuffFormatHookEvent with no files needing reformatting."""
        event = RuffFormatHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            files_reformatted=[],
            files_checked=['test.py'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.ruff-format'
        assert event.status == 'passed'
        assert not event.files_reformatted


class TestRuffFormatRunner:
    """Tests for ruff_format hook runner."""

    def test_ruff_format_runner_returns_typed_event_clean(self) -> None:
        """Test runner returns RuffFormatHookEvent for clean output."""
        clean_output = (FIXTURES_DIR / 'ruff_format_clean.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=clean_output,
                stderr='',
            )

            event = ruff_format_run(['test.py'], 'master', 'ichrisbirch')

            assert isinstance(event, RuffFormatHookEvent)
            assert event.status == 'passed'
            assert event.exit_code == 0
            assert not event.files_reformatted

    def test_ruff_format_runner_parses_changes(self) -> None:
        """Test runner parses files that would be reformatted."""
        changes_output = (FIXTURES_DIR / 'ruff_format_with_changes.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=changes_output,
                stderr='',
            )

            event = ruff_format_run(['ichrisbirch/api/main.py', 'ichrisbirch/models/book.py'], 'master', 'ichrisbirch')

            assert isinstance(event, RuffFormatHookEvent)
            assert event.status == 'failed'
            assert len(event.files_reformatted) == 2
            assert 'ichrisbirch/api/main.py' in event.files_reformatted
            assert 'ichrisbirch/models/book.py' in event.files_reformatted

    def test_ruff_format_runner_skips_non_python_files(self) -> None:
        """Test runner skips non-Python files."""
        event = ruff_format_run(['config.yaml', 'README.md'], 'master', 'ichrisbirch')

        assert event.status == 'passed'
        assert not event.files_checked
