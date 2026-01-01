"""Tests for fixer hooks (trailing-whitespace, end-of-file-fixer, uv-lock, validate-markdown-links)."""

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


class TestUvLockSchema:
    """Tests for UvLockHookEvent schema."""

    def test_uv_lock_hook_event_with_resolution(self) -> None:
        """Test UvLockHookEvent with resolution info."""
        from stats.schemas.hooks.uv_lock import UvLockHookEvent

        event = UvLockHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            packages_resolved=296,
            resolution_time_ms=7,
            files_checked=['pyproject.toml'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.uv-lock'
        assert event.packages_resolved == 296


class TestUvLockRunner:
    """Tests for uv-lock hook runner."""

    def test_uv_lock_runner_parses_resolution(self) -> None:
        """Test runner parses resolution stats from output."""
        from stats.hooks.uv_lock import run
        from stats.schemas.hooks.uv_lock import UvLockHookEvent

        output = (FIXTURES_DIR / 'uv_lock_clean.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=output,
                stderr='',
            )

            event = run(['pyproject.toml'], 'master', 'ichrisbirch')

            assert isinstance(event, UvLockHookEvent)
            assert event.status == 'passed'
            assert event.packages_resolved == 296
            assert event.resolution_time_ms == 7

    def test_uv_lock_runner_skips_non_lock_files(self) -> None:
        """Test runner only checks lock-related files."""
        from stats.hooks.uv_lock import run

        event = run(['main.py', 'README.md'], 'master', 'ichrisbirch')

        assert event.status == 'passed'
        assert not event.files_checked


class TestValidateMarkdownLinksSchema:
    """Tests for ValidateMarkdownLinksHookEvent schema."""

    def test_validate_markdown_links_hook_event_with_issues(self) -> None:
        """Test ValidateMarkdownLinksHookEvent with broken links."""
        from stats.schemas.hooks.validate_markdown_links import BrokenLink
        from stats.schemas.hooks.validate_markdown_links import ValidateMarkdownLinksHookEvent

        event = ValidateMarkdownLinksHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            broken_links=[BrokenLink(path='docs/guide.md', line=15, link='images/missing.png')],
            files_checked=['docs/guide.md'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.validate-markdown-links'
        assert event.status == 'failed'
        assert len(event.broken_links) == 1


class TestValidateMarkdownLinksRunner:
    """Tests for validate-markdown-links hook runner."""

    def test_validate_markdown_links_runner_parses_issues(self) -> None:
        """Test runner parses broken links from output."""
        from stats.hooks.validate_markdown_links import run
        from stats.schemas.hooks.validate_markdown_links import ValidateMarkdownLinksHookEvent

        output = (FIXTURES_DIR / 'validate_markdown_links_with_issues.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=output,
                stderr='',
            )

            event = run(['docs/guide.md'], 'master', 'ichrisbirch')

            assert isinstance(event, ValidateMarkdownLinksHookEvent)
            assert event.status == 'failed'
            assert len(event.broken_links) == 3
            assert event.broken_links[0].path == 'docs/guide.md'
            assert event.broken_links[0].line == 15
            assert event.broken_links[0].link == 'images/screenshot.png'

    def test_validate_markdown_links_runner_filters_md_files(self) -> None:
        """Test runner only checks markdown files."""
        from stats.hooks.validate_markdown_links import run

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')

            event = run(['README.md', 'main.py', 'docs/guide.md'], 'master', 'ichrisbirch')

            assert set(event.files_checked) == {'README.md', 'docs/guide.md'}
