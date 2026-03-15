"""Tests for fixer hooks (trailing-whitespace, end-of-file-fixer)."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


class TestTrailingWhitespaceSchema:
    """Tests for TrailingWhitespaceHookEvent schema."""

    def test_trailing_whitespace_hook_event_with_fixes(self) -> None:
        """Test TrailingWhitespaceHookEvent with fixed files."""
        from stats.schemas.hooks.fixers import TrailingWhitespaceHookEvent

        event = TrailingWhitespaceHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            fixed_files=['main.py', 'utils.py'],
            files_checked=['main.py', 'utils.py', 'config.py'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.trailing-whitespace'
        assert event.status == 'failed'
        assert len(event.fixed_files) == 2


class TestTrailingWhitespaceRunner:
    """Tests for trailing-whitespace hook runner."""

    def test_trailing_whitespace_runner_parses_fixes(self) -> None:
        """Test runner parses fixed files from output."""
        from stats.hooks.trailing_whitespace import run
        from stats.schemas.hooks.fixers import TrailingWhitespaceHookEvent

        fixes_output = (FIXTURES_DIR / 'trailing_whitespace_with_fixes.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=fixes_output,
                stderr='',
            )

            event = run(['main.py'], 'master', 'ichrisbirch')

            assert isinstance(event, TrailingWhitespaceHookEvent)
            assert event.status == 'failed'
            assert len(event.fixed_files) == 3
            assert 'ichrisbirch/api/main.py' in event.fixed_files


class TestEndOfFileFixerSchema:
    """Tests for EndOfFileFixerHookEvent schema."""

    def test_end_of_file_fixer_hook_event_with_fixes(self) -> None:
        """Test EndOfFileFixerHookEvent with fixed files."""
        from stats.schemas.hooks.fixers import EndOfFileFixerHookEvent

        event = EndOfFileFixerHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            fixed_files=['README.md'],
            files_checked=['README.md', 'main.py'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.end-of-file-fixer'
        assert event.status == 'failed'


class TestEndOfFileFixerRunner:
    """Tests for end-of-file-fixer hook runner."""

    def test_end_of_file_fixer_runner_parses_fixes(self) -> None:
        """Test runner parses fixed files from output."""
        from stats.hooks.end_of_file_fixer import run
        from stats.schemas.hooks.fixers import EndOfFileFixerHookEvent

        fixes_output = (FIXTURES_DIR / 'end_of_file_fixer_with_fixes.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=fixes_output,
                stderr='',
            )

            event = run(['README.md'], 'master', 'ichrisbirch')

            assert isinstance(event, EndOfFileFixerHookEvent)
            assert event.status == 'failed'
            assert len(event.fixed_files) == 2
