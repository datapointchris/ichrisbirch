"""Tests for files collector schema and runner."""

from __future__ import annotations

import datetime as dt
import tempfile
from pathlib import Path

from stats.collectors.files import run
from stats.schemas.collectors.files import FilesCollectEvent
from stats.schemas.collectors.files import FileTypeStats


class TestFilesSchema:
    """Tests for FilesCollectEvent schema."""

    def test_file_type_stats_schema(self) -> None:
        """Test FileTypeStats captures all fields."""
        stats = FileTypeStats(
            extension='.py',
            count=100,
            total_size_bytes=1000000,
        )

        assert stats.extension == '.py'
        assert stats.count == 100

    def test_files_collect_event_schema(self) -> None:
        """Test FilesCollectEvent schema."""
        event = FilesCollectEvent(
            timestamp=dt.datetime.now(dt.UTC),
            project='ichrisbirch',
            branch='master',
            file_types=[],
            total_files=0,
            total_size_bytes=0,
            duration_seconds=0.5,
        )

        assert event.type == 'collect.files'


class TestFilesRunner:
    """Tests for files collector runner."""

    def test_files_runner_scans_directory(self) -> None:
        """Test runner scans directory for files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / 'test.py').write_text('# test')
            (Path(tmpdir) / 'test.js').write_text('// test')

            event = run('master', 'ichrisbirch', tmpdir)

            assert isinstance(event, FilesCollectEvent)
            assert event.total_files == 2
