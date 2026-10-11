"""Tests for codespell hook schema and runner."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

from stats.hooks.codespell import run
from stats.schemas.hooks.codespell import CodespellHookEvent
from stats.schemas.hooks.codespell import CodespellIssue

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


class TestCodespellSchema:
    """Tests for CodespellHookEvent schema."""

    def test_codespell_issue_schema(self) -> None:
        """Test that CodespellIssue captures all fields."""
        issue = CodespellIssue(
            filename='test.py',
            line=10,
            word='teh',
            correction='the',
        )

        assert issue.filename == 'test.py'
        assert issue.line == 10
        assert issue.word == 'teh'
        assert issue.correction == 'the'

    def test_codespell_hook_event_with_issues(self) -> None:
        """Test CodespellHookEvent with issues."""
        event = CodespellHookEvent(
            timestamp=dt.datetime.now(dt.UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            issues=[
                CodespellIssue(
                    filename='test.py',
                    line=10,
                    word='teh',
                    correction='the',
                )
            ],
            files_checked=['test.py'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.codespell'
        assert event.status == 'failed'
        assert len(event.issues) == 1

    def test_codespell_hook_event_clean(self) -> None:
        """Test CodespellHookEvent with no issues."""
        event = CodespellHookEvent(
            timestamp=dt.datetime.now(dt.UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            issues=[],
            files_checked=['test.py'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.codespell'
        assert event.status == 'passed'
        assert not event.issues


class TestCodespellRunner:
    """Tests for codespell hook runner."""

    def test_codespell_runner_returns_typed_event_clean(self) -> None:
        """Test runner returns CodespellHookEvent for clean output."""
        clean_output = (FIXTURES_DIR / 'codespell_clean.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=clean_output,
                stderr='',
            )

            event = run(['test.py'], 'master', 'ichrisbirch')

            assert isinstance(event, CodespellHookEvent)
            assert event.status == 'passed'
            assert event.exit_code == 0
            assert not event.issues

    def test_codespell_runner_parses_issues(self) -> None:
        """Test runner parses issues from codespell output."""
        issues_output = (FIXTURES_DIR / 'codespell_with_issues.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=issues_output,
                stderr='',
            )

            event = run(['test.py'], 'master', 'ichrisbirch')

            assert isinstance(event, CodespellHookEvent)
            assert event.status == 'failed'
            assert len(event.issues) == 3
            assert event.issues[0].word == 'teh'
            assert event.issues[0].correction == 'the'

    def test_codespell_runner_measures_duration(self) -> None:
        """Test runner measures execution duration."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='',
                stderr='',
            )

            event = run(['test.py'], 'master', 'ichrisbirch')

            assert event.duration_seconds >= 0
