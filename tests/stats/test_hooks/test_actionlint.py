"""Tests for actionlint hook schema and runner."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


class TestActionlintSchema:
    """Tests for ActionlintHookEvent schema."""

    def test_actionlint_issue_schema(self) -> None:
        """Test that ActionlintIssue captures all fields."""
        from stats.schemas.hooks.actionlint import ActionlintIssue

        issue = ActionlintIssue(
            message='shellcheck reported issue in this script: SC2086',
            filepath='.github/workflows/deploy-project.yml',
            line=34,
            column=9,
            kind='shellcheck',
            snippet='        run: |\\n        ^~~~',
        )

        assert issue.filepath == '.github/workflows/deploy-project.yml'
        assert issue.line == 34
        assert issue.column == 9
        assert issue.kind == 'shellcheck'
        assert 'SC2086' in issue.message

    def test_actionlint_hook_event_with_issues(self) -> None:
        """Test ActionlintHookEvent with issues."""
        from stats.schemas.hooks.actionlint import ActionlintHookEvent
        from stats.schemas.hooks.actionlint import ActionlintIssue

        event = ActionlintHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            issues=[
                ActionlintIssue(
                    message='shellcheck reported issue',
                    filepath='.github/workflows/ci.yml',
                    line=10,
                    column=5,
                    kind='shellcheck',
                    snippet='run: |',
                )
            ],
            files_checked=['.github/workflows/ci.yml'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.actionlint'
        assert event.status == 'failed'
        assert len(event.issues) == 1

    def test_actionlint_hook_event_clean(self) -> None:
        """Test ActionlintHookEvent with no issues."""
        from stats.schemas.hooks.actionlint import ActionlintHookEvent

        event = ActionlintHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            issues=[],
            files_checked=['.github/workflows/ci.yml'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.actionlint'
        assert event.status == 'passed'
        assert not event.issues


class TestActionlintRunner:
    """Tests for actionlint hook runner."""

    def test_actionlint_runner_returns_typed_event_clean(self) -> None:
        """Test runner returns ActionlintHookEvent for clean output."""
        from stats.hooks.actionlint import run
        from stats.schemas.hooks.actionlint import ActionlintHookEvent

        clean_output = (FIXTURES_DIR / 'actionlint_clean.json').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=clean_output,
                stderr='',
            )

            event = run(['.github/workflows/ci.yml'], 'master', 'ichrisbirch')

            assert isinstance(event, ActionlintHookEvent)
            assert event.status == 'passed'
            assert event.exit_code == 0
            assert not event.issues

    def test_actionlint_runner_parses_issues(self) -> None:
        """Test runner parses issues from actionlint JSON output."""
        from stats.hooks.actionlint import run
        from stats.schemas.hooks.actionlint import ActionlintHookEvent

        issues_output = (FIXTURES_DIR / 'actionlint_with_issues.json').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=issues_output,
                stderr='',
            )

            event = run(['.github/workflows/ci.yml'], 'master', 'ichrisbirch')

            assert isinstance(event, ActionlintHookEvent)
            assert event.status == 'failed'
            assert len(event.issues) == 3
            assert event.issues[0].kind == 'shellcheck'
            assert event.issues[0].filepath == '.github/workflows/deploy-project.yml'
            assert event.issues[1].kind == 'workflow-call'
            assert event.issues[2].kind == 'expression'

    def test_actionlint_runner_measures_duration(self) -> None:
        """Test runner measures execution duration."""
        from stats.hooks.actionlint import run

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='[]',
                stderr='',
            )

            event = run(['.github/workflows/ci.yml'], 'master', 'ichrisbirch')

            assert event.duration_seconds >= 0

    def test_actionlint_runner_handles_empty_files_list(self) -> None:
        """Test runner handles empty files list gracefully."""
        from stats.hooks.actionlint import run
        from stats.schemas.hooks.actionlint import ActionlintHookEvent

        event = run([], 'master', 'ichrisbirch')

        assert isinstance(event, ActionlintHookEvent)
        assert event.status == 'passed'
        assert event.exit_code == 0
        assert not event.issues
        assert not event.files_checked

    def test_actionlint_runner_filters_workflow_files(self) -> None:
        """Test runner only checks workflow YAML files."""
        from stats.hooks.actionlint import run

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='[]',
                stderr='',
            )

            event = run(
                [
                    '.github/workflows/ci.yml',
                    'main.py',
                    '.github/workflows/deploy.yaml',
                    'README.md',
                    '.github/dependabot.yml',  # Not in workflows dir
                ],
                'master',
                'ichrisbirch',
            )

            # Should only check .github/workflows/*.yml or .yaml
            assert set(event.files_checked) == {'.github/workflows/ci.yml', '.github/workflows/deploy.yaml'}
