"""Tests for coverage collector schema and runner."""

from __future__ import annotations

import json
import tempfile
from datetime import UTC
from datetime import datetime


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
