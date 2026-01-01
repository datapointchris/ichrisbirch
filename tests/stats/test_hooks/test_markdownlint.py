"""Tests for markdownlint hook schema and runner."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


class TestMarkdownlintSchema:
    """Tests for MarkdownlintHookEvent schema."""

    def test_markdownlint_issue_schema(self) -> None:
        """Test that MarkdownlintIssue captures all fields."""
        from stats.schemas.hooks.markdownlint import MarkdownlintIssue

        issue = MarkdownlintIssue(
            file_name='docs/README.md',
            line_number=10,
            rule_names=['MD009', 'no-trailing-spaces'],
            rule_description='Trailing spaces',
            error_detail='Expected: 0 or 2; Actual: 3',
            error_context=None,
            severity='error',
        )

        assert issue.file_name == 'docs/README.md'
        assert issue.line_number == 10
        assert 'MD009' in issue.rule_names
        assert issue.rule_description == 'Trailing spaces'
        assert issue.severity == 'error'

    def test_markdownlint_hook_event_with_issues(self) -> None:
        """Test MarkdownlintHookEvent with issues."""
        from stats.schemas.hooks.markdownlint import MarkdownlintHookEvent
        from stats.schemas.hooks.markdownlint import MarkdownlintIssue

        event = MarkdownlintHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            issues=[
                MarkdownlintIssue(
                    file_name='docs/README.md',
                    line_number=10,
                    rule_names=['MD009', 'no-trailing-spaces'],
                    rule_description='Trailing spaces',
                    error_detail='Expected: 0 or 2; Actual: 3',
                    error_context=None,
                    severity='error',
                )
            ],
            files_checked=['docs/README.md'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.markdownlint'
        assert event.status == 'failed'
        assert len(event.issues) == 1

    def test_markdownlint_hook_event_clean(self) -> None:
        """Test MarkdownlintHookEvent with no issues."""
        from stats.schemas.hooks.markdownlint import MarkdownlintHookEvent

        event = MarkdownlintHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            issues=[],
            files_checked=['README.md'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.markdownlint'
        assert event.status == 'passed'
        assert not event.issues


class TestMarkdownlintRunner:
    """Tests for markdownlint hook runner."""

    def test_markdownlint_runner_returns_typed_event_clean(self) -> None:
        """Test runner returns MarkdownlintHookEvent for clean output."""
        from stats.hooks.markdownlint import run
        from stats.schemas.hooks.markdownlint import MarkdownlintHookEvent

        clean_output = (FIXTURES_DIR / 'markdownlint_clean.json').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=clean_output,
                stderr='',
            )

            event = run(['README.md'], 'master', 'ichrisbirch')

            assert isinstance(event, MarkdownlintHookEvent)
            assert event.status == 'passed'
            assert event.exit_code == 0
            assert not event.issues

    def test_markdownlint_runner_parses_issues(self) -> None:
        """Test runner parses issues from markdownlint JSON output."""
        from stats.hooks.markdownlint import run
        from stats.schemas.hooks.markdownlint import MarkdownlintHookEvent

        issues_output = (FIXTURES_DIR / 'markdownlint_with_issues.json').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=issues_output,
                stderr='',
            )

            event = run(['docs/README.md', 'CHANGELOG.md'], 'master', 'ichrisbirch')

            assert isinstance(event, MarkdownlintHookEvent)
            assert event.status == 'failed'
            assert len(event.issues) == 3
            assert event.issues[0].file_name == 'docs/README.md'
            assert 'MD041' in event.issues[0].rule_names
            assert event.issues[1].rule_description == 'Trailing spaces'
            assert event.issues[2].severity == 'warning'

    def test_markdownlint_runner_measures_duration(self) -> None:
        """Test runner measures execution duration."""
        from stats.hooks.markdownlint import run

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='',
                stderr='',
            )

            event = run(['README.md'], 'master', 'ichrisbirch')

            assert event.duration_seconds >= 0

    def test_markdownlint_runner_handles_empty_files_list(self) -> None:
        """Test runner handles empty files list gracefully."""
        from stats.hooks.markdownlint import run
        from stats.schemas.hooks.markdownlint import MarkdownlintHookEvent

        event = run([], 'master', 'ichrisbirch')

        assert isinstance(event, MarkdownlintHookEvent)
        assert event.status == 'passed'
        assert event.exit_code == 0
        assert not event.issues
        assert not event.files_checked

    def test_markdownlint_runner_filters_markdown_files(self) -> None:
        """Test runner only checks markdown files."""
        from stats.hooks.markdownlint import run

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='',
                stderr='',
            )

            event = run(['README.md', 'main.py', 'docs/guide.md', 'config.yaml'], 'master', 'ichrisbirch')

            # Should only check .md files
            assert event.files_checked == ['README.md', 'docs/guide.md']
