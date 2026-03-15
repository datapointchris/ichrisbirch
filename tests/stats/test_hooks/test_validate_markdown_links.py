"""Tests for validate-markdown-links hook schema and runner."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


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
