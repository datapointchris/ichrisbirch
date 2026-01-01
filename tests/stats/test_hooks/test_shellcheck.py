"""Tests for shellcheck hook schema and runner."""

from __future__ import annotations

import json
from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


class TestShellcheckSchema:
    """Tests for ShellcheckHookEvent schema."""

    def test_shellcheck_comment_schema_parses_real_output(self) -> None:
        """Test that ShellcheckComment can parse real shellcheck output."""
        from stats.schemas.hooks.shellcheck import ShellcheckComment

        data = json.loads((FIXTURES_DIR / 'shellcheck_with_issues.json').read_text())
        comments = data.get('comments', [])

        if not comments:
            return

        comment = ShellcheckComment.model_validate(comments[0])

        assert comment.code == 2086
        assert comment.level == 'info'
        assert comment.message is not None
        assert comment.fix is not None
        assert len(comment.fix.replacements) == 2

    def test_shellcheck_hook_event_with_issues(self) -> None:
        """Test ShellcheckHookEvent with issues."""
        from stats.schemas.hooks.shellcheck import ShellcheckComment
        from stats.schemas.hooks.shellcheck import ShellcheckHookEvent

        data = json.loads((FIXTURES_DIR / 'shellcheck_with_issues.json').read_text())
        comments = [ShellcheckComment.model_validate(c) for c in data.get('comments', [])]

        event = ShellcheckHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            comments=comments,
            files_checked=['deploy.sh'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.shellcheck'
        assert event.status == 'failed'
        assert len(event.comments) == 2

    def test_shellcheck_hook_event_clean(self) -> None:
        """Test ShellcheckHookEvent with no issues."""
        from stats.schemas.hooks.shellcheck import ShellcheckHookEvent

        event = ShellcheckHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            comments=[],
            files_checked=['deploy.sh'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.shellcheck'
        assert event.status == 'passed'
        assert not event.comments


class TestShellcheckRunner:
    """Tests for shellcheck hook runner."""

    def test_shellcheck_runner_returns_typed_event_clean(self) -> None:
        """Test runner returns ShellcheckHookEvent for clean output."""
        from stats.hooks.shellcheck import run
        from stats.schemas.hooks.shellcheck import ShellcheckHookEvent

        clean_output = (FIXTURES_DIR / 'shellcheck_clean.json').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=clean_output,
                stderr='',
            )

            event = run(['deploy.sh'], 'master', 'ichrisbirch')

            assert isinstance(event, ShellcheckHookEvent)
            assert event.status == 'passed'
            assert event.exit_code == 0
            assert not event.comments

    def test_shellcheck_runner_parses_comments(self) -> None:
        """Test runner parses comments from shellcheck output."""
        from stats.hooks.shellcheck import run
        from stats.schemas.hooks.shellcheck import ShellcheckHookEvent

        issues_output = (FIXTURES_DIR / 'shellcheck_with_issues.json').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=issues_output,
                stderr='',
            )

            event = run(['deploy.sh'], 'master', 'ichrisbirch')

            assert isinstance(event, ShellcheckHookEvent)
            assert event.status == 'failed'
            assert len(event.comments) == 2
            assert event.comments[0].code == 2086

    def test_shellcheck_runner_skips_non_shell_files(self) -> None:
        """Test runner skips non-shell files."""
        from stats.hooks.shellcheck import run

        event = run(['test.py', 'main.js'], 'master', 'ichrisbirch')

        assert event.status == 'passed'
        assert not event.files_checked
