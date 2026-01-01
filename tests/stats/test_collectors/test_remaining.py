"""Tests for remaining collectors (coverage, docker, dependencies, files)."""

from __future__ import annotations

import json
import tempfile
from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch


class TestCoverageSchema:
    """Tests for CoverageCollectEvent schema."""

    def test_coverage_summary_schema(self) -> None:
        """Test CoverageSummary captures all fields."""
        from stats.schemas.collectors.coverage import CoverageSummary

        summary = CoverageSummary(
            covered_lines=1000,
            missing_lines=100,
            excluded_lines=50,
            percent_covered=90.91,
            num_files=25,
        )

        assert summary.covered_lines == 1000
        assert summary.percent_covered == 90.91

    def test_coverage_collect_event_schema(self) -> None:
        """Test CoverageCollectEvent schema."""
        from stats.schemas.collectors.coverage import CoverageCollectEvent
        from stats.schemas.collectors.coverage import CoverageSummary

        event = CoverageCollectEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            summary=CoverageSummary(
                covered_lines=1000,
                missing_lines=100,
                excluded_lines=50,
                percent_covered=90.91,
                num_files=25,
            ),
            files=[],
            duration_seconds=0.5,
        )

        assert event.type == 'collect.coverage'
        assert event.summary.percent_covered == 90.91


class TestCoverageRunner:
    """Tests for coverage collector runner."""

    def test_coverage_runner_returns_none_for_missing_file(self) -> None:
        """Test runner returns None if file doesn't exist."""
        from stats.collectors.coverage import run

        event = run('master', 'ichrisbirch', '/nonexistent/coverage.json')
        assert event is None

    def test_coverage_runner_parses_json(self) -> None:
        """Test runner parses coverage JSON correctly."""
        from stats.collectors.coverage import run
        from stats.schemas.collectors.coverage import CoverageCollectEvent

        coverage_data = {
            'totals': {
                'covered_lines': 1000,
                'missing_lines': 100,
                'excluded_lines': 50,
                'percent_covered': 90.91,
                'num_files': 2,
            },
            'files': {
                'src/main.py': {
                    'summary': {
                        'covered_lines': 500,
                        'missing_lines': 50,
                        'excluded_lines': 25,
                        'percent_covered': 90.91,
                    }
                }
            },
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(coverage_data, f)
            f.flush()

            event = run('master', 'ichrisbirch', f.name)

            assert event is not None
            assert isinstance(event, CoverageCollectEvent)
            assert event.summary.covered_lines == 1000
            assert len(event.files) == 1


class TestDockerSchema:
    """Tests for DockerCollectEvent schema."""

    def test_docker_image_schema(self) -> None:
        """Test DockerImage captures all fields."""
        from stats.schemas.collectors.docker import DockerImage

        image = DockerImage(
            repository='python',
            tag='3.13',
            image_id='abc123',
            created='2025-01-01',
            size='1GB',
        )

        assert image.repository == 'python'
        assert image.tag == '3.13'

    def test_docker_collect_event_schema(self) -> None:
        """Test DockerCollectEvent schema."""
        from stats.schemas.collectors.docker import DockerCollectEvent

        event = DockerCollectEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            images=[],
            containers=[],
            duration_seconds=0.5,
        )

        assert event.type == 'collect.docker'


class TestDependenciesSchema:
    """Tests for DependenciesCollectEvent schema."""

    def test_dependency_schema(self) -> None:
        """Test Dependency captures all fields."""
        from stats.schemas.collectors.dependencies import Dependency

        dep = Dependency(name='pydantic', version='2.0.0')

        assert dep.name == 'pydantic'
        assert dep.version == '2.0.0'

    def test_dependencies_collect_event_schema(self) -> None:
        """Test DependenciesCollectEvent schema."""
        from stats.schemas.collectors.dependencies import DependenciesCollectEvent
        from stats.schemas.collectors.dependencies import Dependency

        event = DependenciesCollectEvent(
            timestamp=datetime.now(UTC),
            project='ichrisbirch',
            branch='master',
            dependencies=[Dependency(name='pydantic', version='2.0.0')],
            total_count=1,
            duration_seconds=0.5,
        )

        assert event.type == 'collect.dependencies'
        assert event.total_count == 1


class TestDependenciesRunner:
    """Tests for dependencies collector runner."""

    def test_dependencies_runner_parses_output(self) -> None:
        """Test runner parses uv pip list output."""
        from stats.collectors.dependencies import run
        from stats.schemas.collectors.dependencies import DependenciesCollectEvent

        mock_output = 'pydantic==2.0.0\nfastapi==0.100.0\n'

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr='',
            )

            event = run('master', 'ichrisbirch')

            assert isinstance(event, DependenciesCollectEvent)
            assert event.total_count == 2
            assert event.dependencies[0].name == 'pydantic'


class TestFilesSchema:
    """Tests for FilesCollectEvent schema."""

    def test_file_type_stats_schema(self) -> None:
        """Test FileTypeStats captures all fields."""
        from stats.schemas.collectors.files import FileTypeStats

        stats = FileTypeStats(
            extension='.py',
            count=100,
            total_size_bytes=1000000,
        )

        assert stats.extension == '.py'
        assert stats.count == 100

    def test_files_collect_event_schema(self) -> None:
        """Test FilesCollectEvent schema."""
        from stats.schemas.collectors.files import FilesCollectEvent

        event = FilesCollectEvent(
            timestamp=datetime.now(UTC),
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
        from stats.collectors.files import run
        from stats.schemas.collectors.files import FilesCollectEvent

        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / 'test.py').write_text('# test')
            (Path(tmpdir) / 'test.js').write_text('// test')

            event = run('master', 'ichrisbirch', tmpdir)

            assert isinstance(event, FilesCollectEvent)
            assert event.total_files == 2
