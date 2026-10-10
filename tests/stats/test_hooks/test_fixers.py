"""Tests for fixer hooks (trailing-whitespace, end-of-file-fixer)."""

from __future__ import annotations

import datetime as dt
import importlib
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


class TestTrailingWhitespaceSchema:
    """Tests for TrailingWhitespaceHookEvent schema."""

    def test_trailing_whitespace_hook_event_with_fixes(self) -> None:
        """Test TrailingWhitespaceHookEvent with fixed files."""
        from stats.schemas.hooks.fixers import TrailingWhitespaceHookEvent

        event = TrailingWhitespaceHookEvent(
            timestamp=dt.datetime.now(dt.UTC),
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

    def test_trailing_whitespace_runner_parses_fixes(self, tmp_path: Path) -> None:
        """Test runner parses fixed files from output."""
        from stats.hooks.trailing_whitespace import run
        from stats.schemas.hooks.fixers import TrailingWhitespaceHookEvent

        fixes_output = (FIXTURES_DIR / 'trailing_whitespace_with_fixes.txt').read_text()
        source = tmp_path / 'main.py'
        source.write_text('x = 1\n')

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=fixes_output,
                stderr='',
            )

            event = run([str(source)], 'master', 'ichrisbirch')

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
            timestamp=dt.datetime.now(dt.UTC),
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

    def test_end_of_file_fixer_runner_parses_fixes(self, tmp_path: Path) -> None:
        """Test runner parses fixed files from output."""
        from stats.hooks.end_of_file_fixer import run
        from stats.schemas.hooks.fixers import EndOfFileFixerHookEvent

        fixes_output = (FIXTURES_DIR / 'end_of_file_fixer_with_fixes.txt').read_text()
        readme = tmp_path / 'README.md'
        readme.write_text('# Title\n')

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=fixes_output,
                stderr='',
            )

            event = run([str(readme)], 'master', 'ichrisbirch')

            assert isinstance(event, EndOfFileFixerHookEvent)
            assert event.status == 'failed'
            assert len(event.fixed_files) == 2


# A PNG signature and the start of a chunk, holding a space before a newline byte
# that a whitespace fixer would strip.
PNG_BYTES = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR \n\x00\x01'


@pytest.mark.parametrize('module', ['stats.hooks.trailing_whitespace', 'stats.hooks.end_of_file_fixer'])
class TestFixersLeaveBinariesAlone:
    """The fixers rewrite what they are given, so a binary never reaches them."""

    def test_a_staged_binary_is_not_handed_to_the_fixer(self, module: str, tmp_path: Path) -> None:
        image = tmp_path / 'icon.png'
        image.write_bytes(PNG_BYTES)
        source = tmp_path / 'main.py'
        source.write_text('x = 1\n')

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
            event = importlib.import_module(module).run([str(image), str(source)], 'master', 'ichrisbirch')

        argv = mock_run.call_args.args[0]
        assert (str(image) in argv, str(source) in argv) == (False, True)
        assert event.files_checked == [str(source)]

    def test_only_binaries_staged_runs_no_fixer(self, module: str, tmp_path: Path) -> None:
        image = tmp_path / 'icon.png'
        image.write_bytes(PNG_BYTES)

        with patch('subprocess.run') as mock_run:
            event = importlib.import_module(module).run([str(image)], 'master', 'ichrisbirch')

        mock_run.assert_not_called()
        assert (event.status, event.files_checked) == ('passed', [])
