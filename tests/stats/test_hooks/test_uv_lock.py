"""Tests for uv-lock hook schema and runner."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


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
