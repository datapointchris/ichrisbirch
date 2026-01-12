"""Coverage collector runner - reads coverage.py JSON report."""

from __future__ import annotations

import json
from datetime import UTC
from datetime import datetime
from pathlib import Path

from stats.schemas.collectors.coverage import CoverageCollectEvent
from stats.schemas.collectors.coverage import CoverageFileSummary
from stats.schemas.collectors.coverage import CoverageSummary


def run(branch: str, project: str, json_path: str = '.coverage.json') -> CoverageCollectEvent | None:
    """Read coverage JSON report and return fully-typed event.

    Args:
        branch: Current git branch
        project: Project name
        json_path: Path to coverage JSON report

    Returns:
        CoverageCollectEvent with coverage data, or None if file not found
    """
    path = Path(json_path)
    if not path.exists():
        return None

    with path.open() as f:
        raw_data = json.load(f)

    totals = raw_data.get('totals', {})
    files_data = raw_data.get('files', {})

    files = [
        CoverageFileSummary(
            filename=filename,
            covered_lines=data.get('summary', {}).get('covered_lines', 0),
            missing_lines=data.get('summary', {}).get('missing_lines', 0),
            excluded_lines=data.get('summary', {}).get('excluded_lines', 0),
            percent_covered=data.get('summary', {}).get('percent_covered', 0.0),
        )
        for filename, data in files_data.items()
    ]

    summary = CoverageSummary(
        covered_lines=totals.get('covered_lines', 0),
        missing_lines=totals.get('missing_lines', 0),
        excluded_lines=totals.get('excluded_lines', 0),
        percent_covered=totals.get('percent_covered', 0.0),
        num_files=totals.get('num_files', len(files)),
    )

    return CoverageCollectEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        summary=summary,
        files=files,
        duration_seconds=0.0,
    )
