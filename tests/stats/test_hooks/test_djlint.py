"""Tests for djlint hook schema and runner."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


class TestDjlintSchema:
    """Tests for DjlintHookEvent schema."""

    def test_djlint_issue_schema(self) -> None:
        """Test that DjlintIssue captures all fields."""
        from stats.schemas.hooks.djlint import DjlintIssue

        issue = DjlintIssue(
            path='ichrisbirch/app/templates/base.html',
            line=2,
            column=0,
            code='H005',
            message='Html tag should have lang attribute.',
        )

        assert issue.path == 'ichrisbirch/app/templates/base.html'
        assert issue.line == 2
        assert issue.column == 0
        assert issue.code == 'H005'
        assert 'lang attribute' in issue.message

    def test_djlint_hook_event_with_issues(self) -> None:
        """Test DjlintHookEvent with issues."""
        from stats.schemas.hooks.djlint import DjlintHookEvent
        from stats.schemas.hooks.djlint import DjlintIssue

        event = DjlintHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            issues=[
                DjlintIssue(
                    path='ichrisbirch/app/templates/base.html',
                    line=2,
                    column=0,
                    code='H005',
                    message='Html tag should have lang attribute.',
                )
            ],
            files_checked=['ichrisbirch/app/templates/base.html'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.djlint'
        assert event.status == 'failed'
        assert len(event.issues) == 1

    def test_djlint_hook_event_clean(self) -> None:
        """Test DjlintHookEvent with no issues."""
        from stats.schemas.hooks.djlint import DjlintHookEvent

        event = DjlintHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            issues=[],
            files_checked=['ichrisbirch/app/templates/base.html'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.djlint'
        assert event.status == 'passed'
        assert not event.issues


class TestDjlintRunner:
    """Tests for djlint hook runner."""

    def test_djlint_runner_returns_typed_event_clean(self) -> None:
        """Test runner returns DjlintHookEvent for clean output."""
        from stats.hooks.djlint import run
        from stats.schemas.hooks.djlint import DjlintHookEvent

        clean_output = (FIXTURES_DIR / 'djlint_clean.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=clean_output,
                stderr='',
            )

            event = run(['template.html'], 'master', 'ichrisbirch')

            assert isinstance(event, DjlintHookEvent)
            assert event.status == 'passed'
            assert event.exit_code == 0
            assert not event.issues

    def test_djlint_runner_parses_issues(self) -> None:
        """Test runner parses issues from djlint output."""
        from stats.hooks.djlint import run
        from stats.schemas.hooks.djlint import DjlintHookEvent

        issues_output = (FIXTURES_DIR / 'djlint_with_issues.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=issues_output,
                stderr='',
            )

            event = run(['base.html', 'index.html'], 'master', 'ichrisbirch')

            assert isinstance(event, DjlintHookEvent)
            assert event.status == 'failed'
            assert len(event.issues) == 5
            assert event.issues[0].code == 'H005'
            assert event.issues[0].path == 'ichrisbirch/app/templates/base.html'
            assert event.issues[0].line == 2
            assert event.issues[2].path == 'ichrisbirch/app/templates/tasks/index.html'
            assert event.issues[2].code == 'H006'

    def test_djlint_runner_measures_duration(self) -> None:
        """Test runner measures execution duration."""
        from stats.hooks.djlint import run

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='Linted 1 file, found 0 errors.',
                stderr='',
            )

            event = run(['template.html'], 'master', 'ichrisbirch')

            assert event.duration_seconds >= 0

    def test_djlint_runner_handles_empty_files_list(self) -> None:
        """Test runner handles empty files list gracefully."""
        from stats.hooks.djlint import run
        from stats.schemas.hooks.djlint import DjlintHookEvent

        event = run([], 'master', 'ichrisbirch')

        assert isinstance(event, DjlintHookEvent)
        assert event.status == 'passed'
        assert event.exit_code == 0
        assert not event.issues
        assert not event.files_checked

    def test_djlint_runner_filters_html_files(self) -> None:
        """Test runner only checks HTML/Jinja files."""
        from stats.hooks.djlint import run

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='',
                stderr='',
            )

            event = run(['template.html', 'main.py', 'page.jinja', 'config.yaml', 'form.jinja2'], 'master', 'ichrisbirch')

            # Should only check .html, .jinja, .jinja2 files
            assert set(event.files_checked) == {'template.html', 'page.jinja', 'form.jinja2'}
