"""Tests for refurb hook schema and runner."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


class TestRefurbSchema:
    """Tests for RefurbHookEvent schema."""

    def test_refurb_issue_schema(self) -> None:
        """Test that RefurbIssue captures all fields."""
        from stats.schemas.hooks.refurb import RefurbIssue

        issue = RefurbIssue(
            path='ichrisbirch/api/main.py',
            line=6,
            column=14,
            code='FURB110',
            message='Replace `x if x else "default"` with `x or "default"`',
        )

        assert issue.path == 'ichrisbirch/api/main.py'
        assert issue.line == 6
        assert issue.column == 14
        assert issue.code == 'FURB110'
        assert 'Replace' in issue.message

    def test_refurb_hook_event_with_issues(self) -> None:
        """Test RefurbHookEvent with issues."""
        from stats.schemas.hooks.refurb import RefurbHookEvent
        from stats.schemas.hooks.refurb import RefurbIssue

        event = RefurbHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            issues=[
                RefurbIssue(
                    path='ichrisbirch/api/main.py',
                    line=6,
                    column=14,
                    code='FURB110',
                    message='Replace `x if x else "default"` with `x or "default"`',
                )
            ],
            files_checked=['ichrisbirch/api/main.py'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.refurb'
        assert event.status == 'failed'
        assert len(event.issues) == 1

    def test_refurb_hook_event_clean(self) -> None:
        """Test RefurbHookEvent with no issues."""
        from stats.schemas.hooks.refurb import RefurbHookEvent

        event = RefurbHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            issues=[],
            files_checked=['ichrisbirch/api/main.py'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.refurb'
        assert event.status == 'passed'
        assert not event.issues


class TestRefurbRunner:
    """Tests for refurb hook runner."""

    def test_refurb_runner_returns_typed_event_clean(self) -> None:
        """Test runner returns RefurbHookEvent for clean output."""
        from stats.hooks.refurb import run
        from stats.schemas.hooks.refurb import RefurbHookEvent

        clean_output = (FIXTURES_DIR / 'refurb_clean.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=clean_output,
                stderr='',
            )

            event = run(['test.py'], 'master', 'ichrisbirch')

            assert isinstance(event, RefurbHookEvent)
            assert event.status == 'passed'
            assert event.exit_code == 0
            assert not event.issues

    def test_refurb_runner_parses_issues(self) -> None:
        """Test runner parses issues from refurb output."""
        from stats.hooks.refurb import run
        from stats.schemas.hooks.refurb import RefurbHookEvent

        issues_output = (FIXTURES_DIR / 'refurb_with_issues.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=issues_output,
                stderr='',
            )

            event = run(['test.py'], 'master', 'ichrisbirch')

            assert isinstance(event, RefurbHookEvent)
            assert event.status == 'failed'
            assert len(event.issues) == 3
            assert event.issues[0].code == 'FURB110'
            assert event.issues[0].path == 'ichrisbirch/api/main.py'
            assert event.issues[0].line == 6
            assert event.issues[0].column == 14
            assert event.issues[1].code == 'FURB146'
            assert event.issues[2].code == 'FURB103'

    def test_refurb_runner_measures_duration(self) -> None:
        """Test runner measures execution duration."""
        from stats.hooks.refurb import run

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='',
                stderr='',
            )

            event = run(['test.py'], 'master', 'ichrisbirch')

            assert event.duration_seconds >= 0

    def test_refurb_runner_handles_empty_files_list(self) -> None:
        """Test runner handles empty files list gracefully."""
        from stats.hooks.refurb import run
        from stats.schemas.hooks.refurb import RefurbHookEvent

        event = run([], 'master', 'ichrisbirch')

        assert isinstance(event, RefurbHookEvent)
        assert event.status == 'passed'
        assert event.exit_code == 0
        assert not event.issues
        assert not event.files_checked
