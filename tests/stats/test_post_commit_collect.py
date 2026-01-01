"""Tests for post-commit collect script."""

from __future__ import annotations

import tempfile
from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch


class TestGetBranch:
    """Tests for get_branch function."""

    def test_get_branch_returns_branch_name(self) -> None:
        """Test get_branch returns the current branch name."""
        from stats.post_commit_collect import get_branch

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout='master\n',
                returncode=0,
            )

            branch = get_branch()

            assert branch == 'master'

    def test_get_branch_returns_head_when_empty(self) -> None:
        """Test get_branch returns HEAD when branch is empty."""
        from stats.post_commit_collect import get_branch

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout='',
                returncode=0,
            )

            branch = get_branch()

            assert branch == 'HEAD'


class TestGetCommitInfo:
    """Tests for get_commit_info function."""

    def test_get_commit_info_parses_git_log(self) -> None:
        """Test get_commit_info parses git log output correctly."""
        from stats.post_commit_collect import get_commit_info

        with patch('subprocess.run') as mock_run:
            git_log_output = (
                'abc123def456789012345678901234567890abcd|abc123d|feat: add feature|'
                'Chris Birch|datapointchris@gmail.com|2025-12-31T12:00:00-05:00\n'
            )
            mock_run.side_effect = [
                MagicMock(
                    stdout=git_log_output,
                    returncode=0,
                ),
                MagicMock(
                    stdout=' 3 files changed, 100 insertions(+), 50 deletions(-)\n',
                    returncode=0,
                ),
            ]

            info = get_commit_info()

            assert info['hash'] == 'abc123def456789012345678901234567890abcd'
            assert info['short_hash'] == 'abc123d'
            assert info['message'] == 'feat: add feature'
            assert info['author'] == 'Chris Birch'
            assert info['email'] == 'datapointchris@gmail.com'
            assert info['files_changed'] == 3
            assert info['insertions'] == 100
            assert info['deletions'] == 50


class TestGetStagedFilesFromCommit:
    """Tests for get_staged_files_from_commit function."""

    def test_get_staged_files_parses_numstat(self) -> None:
        """Test get_staged_files_from_commit parses git numstat output."""
        from stats.post_commit_collect import get_staged_files_from_commit

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout='10\t5\ttest.py\n50\t0\tnew.py\n0\t30\told.py\n',
                returncode=0,
            )

            files = get_staged_files_from_commit()

            assert len(files) == 3
            assert files[0].path == 'test.py'
            assert files[0].status == 'modified'
            assert files[0].lines_added == 10
            assert files[0].lines_removed == 5

            assert files[1].path == 'new.py'
            assert files[1].status == 'added'
            assert files[1].lines_added == 50
            assert files[1].lines_removed == 0

            assert files[2].path == 'old.py'
            assert files[2].status == 'deleted'
            assert files[2].lines_added == 0
            assert files[2].lines_removed == 30

    def test_get_staged_files_empty(self) -> None:
        """Test get_staged_files_from_commit handles empty output."""
        from stats.post_commit_collect import get_staged_files_from_commit

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout='',
                returncode=0,
            )

            files = get_staged_files_from_commit()

            assert not files


class TestMain:
    """Tests for main function."""

    def test_main_emits_commit_event(self) -> None:
        """Test main emits a commit event."""
        from stats.post_commit_collect import main

        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / 'events.jsonl'

            with (
                patch('stats.post_commit_collect.load_config') as mock_config,
                patch('stats.post_commit_collect.get_branch') as mock_branch,
                patch('stats.post_commit_collect.get_commit_info') as mock_commit_info,
                patch('stats.post_commit_collect.get_staged_files_from_commit') as mock_staged,
            ):
                mock_config.return_value = {
                    'project': 'ichrisbirch',
                    'events_path': str(events_path),
                    'collect': {'collectors': []},
                }
                mock_branch.return_value = 'master'
                mock_commit_info.return_value = {
                    'hash': 'abc123def456789012345678901234567890abcd',
                    'short_hash': 'abc123d',
                    'message': 'feat: add feature',
                    'author': 'Chris Birch',
                    'email': 'datapointchris@gmail.com',
                    'timestamp': '2025-12-31T12:00:00-05:00',
                    'files_changed': 1,
                    'insertions': 10,
                    'deletions': 5,
                }
                mock_staged.return_value = []

                result = main()

                assert result == 0
                assert events_path.exists()
                content = events_path.read_text()
                assert '"type":"commit"' in content

    def test_main_runs_enabled_collectors(self) -> None:
        """Test main runs the enabled collectors."""
        from stats.post_commit_collect import main
        from stats.schemas.collectors.tokei import TokeiCollectEvent

        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / 'events.jsonl'

            with (
                patch('stats.post_commit_collect.load_config') as mock_config,
                patch('stats.post_commit_collect.get_branch') as mock_branch,
                patch('stats.post_commit_collect.get_commit_info') as mock_commit_info,
                patch('stats.post_commit_collect.get_staged_files_from_commit') as mock_staged,
                patch('stats.collectors.tokei.run') as mock_tokei_run,
            ):
                mock_config.return_value = {
                    'project': 'ichrisbirch',
                    'events_path': str(events_path),
                    'collect': {'collectors': ['tokei']},
                }
                mock_branch.return_value = 'master'
                mock_commit_info.return_value = {
                    'hash': 'abc123',
                    'short_hash': 'abc',
                    'message': 'test',
                    'author': 'Test',
                    'email': 'test@test.com',
                    'timestamp': '2025-12-31T12:00:00-05:00',
                    'files_changed': 1,
                    'insertions': 10,
                    'deletions': 5,
                }
                mock_staged.return_value = []
                mock_tokei_run.return_value = TokeiCollectEvent(
                    timestamp=datetime.now(UTC),
                    project='ichrisbirch',
                    branch='master',
                    total_files=100,
                    total_lines=10000,
                    total_code=8000,
                    total_comments=1000,
                    total_blanks=1000,
                    languages={},
                    duration_seconds=0.5,
                )

                result = main()

                assert result == 0
                lines = events_path.read_text().strip().split('\n')
                assert len(lines) == 2
                assert 'commit' in lines[0]
                assert 'collect.tokei' in lines[1]

    def test_main_skips_unknown_collectors(self, capsys) -> None:
        """Test main skips unknown collectors with a warning."""
        from stats.post_commit_collect import main

        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / 'events.jsonl'

            with (
                patch('stats.post_commit_collect.load_config') as mock_config,
                patch('stats.post_commit_collect.get_branch') as mock_branch,
                patch('stats.post_commit_collect.get_commit_info') as mock_commit_info,
                patch('stats.post_commit_collect.get_staged_files_from_commit') as mock_staged,
            ):
                mock_config.return_value = {
                    'project': 'ichrisbirch',
                    'events_path': str(events_path),
                    'collect': {'collectors': ['nonexistent_collector']},
                }
                mock_branch.return_value = 'master'
                mock_commit_info.return_value = {
                    'hash': 'abc123',
                    'short_hash': 'abc',
                    'message': 'test',
                    'author': 'Test',
                    'email': 'test@test.com',
                    'timestamp': '2025-12-31T12:00:00-05:00',
                    'files_changed': 1,
                    'insertions': 10,
                    'deletions': 5,
                }
                mock_staged.return_value = []

                result = main()

                assert result == 0
                captured = capsys.readouterr()
                assert 'nonexistent_collector' in captured.out
                assert 'skipping' in captured.out.lower()

    def test_main_handles_collector_returning_none(self) -> None:
        """Test main handles collectors that return None (e.g., no pytest report)."""
        from stats.post_commit_collect import main

        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / 'events.jsonl'

            with (
                patch('stats.post_commit_collect.load_config') as mock_config,
                patch('stats.post_commit_collect.get_branch') as mock_branch,
                patch('stats.post_commit_collect.get_commit_info') as mock_commit_info,
                patch('stats.post_commit_collect.get_staged_files_from_commit') as mock_staged,
                patch('stats.collectors.pytest_collector.run') as mock_pytest_run,
            ):
                mock_config.return_value = {
                    'project': 'ichrisbirch',
                    'events_path': str(events_path),
                    'collect': {'collectors': ['pytest_collector']},
                }
                mock_branch.return_value = 'master'
                mock_commit_info.return_value = {
                    'hash': 'abc123',
                    'short_hash': 'abc',
                    'message': 'test',
                    'author': 'Test',
                    'email': 'test@test.com',
                    'timestamp': '2025-12-31T12:00:00-05:00',
                    'files_changed': 1,
                    'insertions': 10,
                    'deletions': 5,
                }
                mock_staged.return_value = []
                mock_pytest_run.return_value = None

                result = main()

                assert result == 0
                lines = events_path.read_text().strip().split('\n')
                assert len(lines) == 1
                assert 'commit' in lines[0]
