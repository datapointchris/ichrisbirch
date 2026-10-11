"""Tests for the actionlint hook runner."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

from stats.hooks.actionlint import run
from stats.schemas.hooks.actionlint import ActionlintHookEvent

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


class TestActionlintRunner:
    """Tests for actionlint hook runner."""

    def test_actionlint_runner_returns_typed_event_clean(self) -> None:
        """Test runner returns ActionlintHookEvent for clean output."""
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
            assert event.issues[0].filepath == '.github/workflows/release.yml'
            assert event.issues[1].kind == 'workflow-call'
            assert event.issues[2].kind == 'expression'

    def test_actionlint_runner_measures_duration(self) -> None:
        """Test runner measures execution duration."""
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
        event = run([], 'master', 'ichrisbirch')

        assert isinstance(event, ActionlintHookEvent)
        assert event.status == 'passed'
        assert event.exit_code == 0
        assert not event.issues
        assert not event.files_checked

    def test_actionlint_runner_filters_workflow_files(self) -> None:
        """Test runner only checks workflow YAML files."""
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
