"""Dependencies collector runner - captures Python dependencies."""

from __future__ import annotations

import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.collectors.dependencies import DependenciesCollectEvent
from stats.schemas.collectors.dependencies import Dependency


def run(branch: str, project: str) -> DependenciesCollectEvent:
    """Collect Python dependencies, return fully-typed event.

    Args:
        branch: Current git branch
        project: Project name

    Returns:
        DependenciesCollectEvent with dependency info
    """
    start_time = time.perf_counter()

    result = subprocess.run(  # nosec B603 B607
        ['uv', 'pip', 'list', '--format=freeze'],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time

    dependencies = []
    for line in result.stdout.strip().split('\n'):
        if not line or '==' not in line:
            continue
        parts = line.split('==')
        if len(parts) >= 2:
            dependencies.append(
                Dependency(
                    name=parts[0].strip(),
                    version=parts[1].strip(),
                )
            )

    return DependenciesCollectEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        dependencies=dependencies,
        total_count=len(dependencies),
        duration_seconds=round(duration, 3),
    )
