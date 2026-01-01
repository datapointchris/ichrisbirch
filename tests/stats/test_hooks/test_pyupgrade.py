"""Tests for pyupgrade hook schema and runner."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'tool_outputs'


class TestPyupgradeSchema:
    """Tests for PyupgradeHookEvent schema."""

    def test_pyupgrade_hook_event_with_rewrites(self) -> None:
        """Test PyupgradeHookEvent with rewritten files."""
        from stats.schemas.hooks.pyupgrade import PyupgradeHookEvent

        event = PyupgradeHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='failed',
            exit_code=1,
            rewritten_files=['ichrisbirch/api/main.py', 'ichrisbirch/models/user.py'],
            files_checked=['ichrisbirch/api/main.py', 'ichrisbirch/models/user.py', 'ichrisbirch/app/routes.py'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.pyupgrade'
        assert event.status == 'failed'
        assert len(event.rewritten_files) == 2
        assert 'ichrisbirch/api/main.py' in event.rewritten_files

    def test_pyupgrade_hook_event_clean(self) -> None:
        """Test PyupgradeHookEvent with no rewrites."""
        from stats.schemas.hooks.pyupgrade import PyupgradeHookEvent

        event = PyupgradeHookEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            status='passed',
            exit_code=0,
            rewritten_files=[],
            files_checked=['ichrisbirch/api/main.py'],
            duration_seconds=0.5,
        )

        assert event.type == 'hook.pyupgrade'
        assert event.status == 'passed'
        assert not event.rewritten_files


class TestPyupgradeRunner:
    """Tests for pyupgrade hook runner."""

    def test_pyupgrade_runner_returns_typed_event_clean(self) -> None:
        """Test runner returns PyupgradeHookEvent for clean output."""
        from stats.hooks.pyupgrade import run
        from stats.schemas.hooks.pyupgrade import PyupgradeHookEvent

        clean_output = (FIXTURES_DIR / 'pyupgrade_clean.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=clean_output,
                stderr='',
            )

            event = run(['test.py'], 'master', 'ichrisbirch')

            assert isinstance(event, PyupgradeHookEvent)
            assert event.status == 'passed'
            assert event.exit_code == 0
            assert not event.rewritten_files

    def test_pyupgrade_runner_parses_rewrites(self) -> None:
        """Test runner parses rewritten files from pyupgrade output."""
        from stats.hooks.pyupgrade import run
        from stats.schemas.hooks.pyupgrade import PyupgradeHookEvent

        rewrites_output = (FIXTURES_DIR / 'pyupgrade_with_rewrites.txt').read_text()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=rewrites_output,
                stderr='',
            )

            event = run(['test.py'], 'master', 'ichrisbirch')

            assert isinstance(event, PyupgradeHookEvent)
            assert event.status == 'failed'
            assert len(event.rewritten_files) == 3
            assert 'ichrisbirch/api/main.py' in event.rewritten_files
            assert 'ichrisbirch/models/user.py' in event.rewritten_files
            assert 'stats/collectors/radon.py' in event.rewritten_files

    def test_pyupgrade_runner_measures_duration(self) -> None:
        """Test runner measures execution duration."""
        from stats.hooks.pyupgrade import run

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='',
                stderr='',
            )

            event = run(['test.py'], 'master', 'ichrisbirch')

            assert event.duration_seconds >= 0

    def test_pyupgrade_runner_handles_empty_files_list(self) -> None:
        """Test runner handles empty files list gracefully."""
        from stats.hooks.pyupgrade import run
        from stats.schemas.hooks.pyupgrade import PyupgradeHookEvent

        event = run([], 'master', 'ichrisbirch')

        assert isinstance(event, PyupgradeHookEvent)
        assert event.status == 'passed'
        assert event.exit_code == 0
        assert not event.rewritten_files
        assert not event.files_checked

    def test_pyupgrade_runner_filters_python_files(self) -> None:
        """Test runner only checks Python files."""
        from stats.hooks.pyupgrade import run

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='',
                stderr='',
            )

            event = run(['test.py', 'README.md', 'main.py', 'config.yaml'], 'master', 'ichrisbirch')

            # Should only check .py files
            assert event.files_checked == ['test.py', 'main.py']
