"""Tests for pre-commit capture script."""

from __future__ import annotations

import tempfile
from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch


class TestGetStagedFiles:
    """Tests for get_staged_files function."""

    def test_get_staged_files_returns_list(self) -> None:
        """Test get_staged_files returns a list of staged files."""
        from stats.pre_commit_capture import get_staged_files

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout='file1.py\nfile2.py\nfile3.py\n',
                returncode=0,
            )

            files = get_staged_files()

            assert files == ['file1.py', 'file2.py', 'file3.py']

    def test_get_staged_files_empty(self) -> None:
        """Test get_staged_files returns empty list when no staged files."""
        from stats.pre_commit_capture import get_staged_files

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout='',
                returncode=0,
            )

            files = get_staged_files()

            assert not files


class TestGetBranch:
    """Tests for get_branch function."""

    def test_get_branch_returns_branch_name(self) -> None:
        """Test get_branch returns the current branch name."""
        from stats.pre_commit_capture import get_branch

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout='feature-branch\n',
                returncode=0,
            )

            branch = get_branch()

            assert branch == 'feature-branch'

    def test_get_branch_returns_head_when_empty(self) -> None:
        """Test get_branch returns HEAD when branch is empty (detached HEAD)."""
        from stats.pre_commit_capture import get_branch

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout='',
                returncode=0,
            )

            branch = get_branch()

            assert branch == 'HEAD'


class TestMain:
    """Tests for main function."""

    def test_main_returns_zero_when_no_staged_files(self) -> None:
        """Test main returns 0 when no files are staged."""
        from stats.pre_commit_capture import main

        with (
            patch('stats.pre_commit_capture.load_config') as mock_config,
            patch('stats.pre_commit_capture.get_staged_files') as mock_staged,
        ):
            mock_config.return_value = {
                'project': 'ichrisbirch',
                'events_path': '/tmp/events.jsonl',
                'capture': {'hooks': ['ruff']},
            }
            mock_staged.return_value = []

            result = main()

            assert result == 0

    def test_main_runs_enabled_hooks(self) -> None:
        """Test main runs the enabled hooks."""
        from stats.pre_commit_capture import main
        from stats.schemas.hooks.ruff import RuffHookEvent

        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / 'events.jsonl'

            with (
                patch('stats.pre_commit_capture.load_config') as mock_config,
                patch('stats.pre_commit_capture.get_staged_files') as mock_staged,
                patch('stats.pre_commit_capture.get_branch') as mock_branch,
                patch('stats.hooks.ruff.run') as mock_ruff_run,
            ):
                mock_config.return_value = {
                    'project': 'ichrisbirch',
                    'events_path': str(events_path),
                    'capture': {'hooks': ['ruff']},
                }
                mock_staged.return_value = ['test.py']
                mock_branch.return_value = 'master'
                mock_ruff_run.return_value = RuffHookEvent(
                    timestamp=datetime.now(UTC),
                    project='ichrisbirch',
                    branch='master',
                    status='passed',
                    exit_code=0,
                    issues=[],
                    files_checked=['test.py'],
                    duration_seconds=0.5,
                )

                result = main()

                assert result == 0
                assert events_path.exists()
                mock_ruff_run.assert_called_once_with(['test.py'], 'master', 'ichrisbirch')

    def test_main_skips_unknown_hooks(self, capsys) -> None:
        """Test main skips unknown hooks with a warning."""
        from stats.pre_commit_capture import main

        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / 'events.jsonl'

            with (
                patch('stats.pre_commit_capture.load_config') as mock_config,
                patch('stats.pre_commit_capture.get_staged_files') as mock_staged,
                patch('stats.pre_commit_capture.get_branch') as mock_branch,
            ):
                mock_config.return_value = {
                    'project': 'ichrisbirch',
                    'events_path': str(events_path),
                    'capture': {'hooks': ['nonexistent_hook']},
                }
                mock_staged.return_value = ['test.py']
                mock_branch.return_value = 'master'

                result = main()

                assert result == 0
                captured = capsys.readouterr()
                assert 'nonexistent_hook' in captured.out
                assert 'skipping' in captured.out.lower()

    def test_main_emits_events_for_multiple_hooks(self) -> None:
        """Test main emits events for each hook."""
        from stats.pre_commit_capture import main
        from stats.schemas.hooks.mypy import MypyHookEvent
        from stats.schemas.hooks.ruff import RuffHookEvent

        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / 'events.jsonl'

            with (
                patch('stats.pre_commit_capture.load_config') as mock_config,
                patch('stats.pre_commit_capture.get_staged_files') as mock_staged,
                patch('stats.pre_commit_capture.get_branch') as mock_branch,
                patch('stats.hooks.ruff.run') as mock_ruff_run,
                patch('stats.hooks.mypy.run') as mock_mypy_run,
            ):
                mock_config.return_value = {
                    'project': 'ichrisbirch',
                    'events_path': str(events_path),
                    'capture': {'hooks': ['ruff', 'mypy']},
                }
                mock_staged.return_value = ['test.py']
                mock_branch.return_value = 'master'
                mock_ruff_run.return_value = RuffHookEvent(
                    timestamp=datetime.now(UTC),
                    project='ichrisbirch',
                    branch='master',
                    status='passed',
                    exit_code=0,
                    issues=[],
                    files_checked=['test.py'],
                    duration_seconds=0.5,
                )
                mock_mypy_run.return_value = MypyHookEvent(
                    timestamp=datetime.now(UTC),
                    project='ichrisbirch',
                    branch='master',
                    status='passed',
                    exit_code=0,
                    errors=[],
                    files_checked=['test.py'],
                    duration_seconds=0.3,
                )

                result = main()

                assert result == 0
                lines = events_path.read_text().strip().split('\n')
                assert len(lines) == 2
                assert 'hook.ruff' in lines[0]
                assert 'hook.mypy' in lines[1]
