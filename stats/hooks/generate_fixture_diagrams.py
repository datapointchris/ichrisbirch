"""Generate-fixture-diagrams hook runner - captures diagram generation."""

from __future__ import annotations

import re
import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.project import GenerateFixtureDiagramsHookEvent

# Files that trigger diagram regeneration
RELEVANT_PATTERN = re.compile(r'(tests/conftest\.py|tests/utils/.*|mkdocs_plugins/diagrams/.*\.py)$')


def run(staged_files: list[str], branch: str, project: str) -> GenerateFixtureDiagramsHookEvent:
    """Run generate-fixture-diagrams if relevant files are staged, return fully-typed event."""
    start_time = time.perf_counter()

    relevant_files = [f for f in staged_files if RELEVANT_PATTERN.search(f)]

    if not relevant_files:
        return GenerateFixtureDiagramsHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            files_checked=[],
            duration_seconds=0.0,
        )

    result = subprocess.run(  # nosec B603 B607
        ['uv', 'run', 'python', '-m', 'mkdocs_plugins.diagrams', '--output-dir', '/tmp/devstats-diagrams'],  # nosec B108
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time

    return GenerateFixtureDiagramsHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        files_checked=relevant_files,
        duration_seconds=round(duration, 3),
    )
