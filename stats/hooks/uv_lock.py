"""UV lock hook runner - captures dependency resolution stats."""

from __future__ import annotations

import re
import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.uv_lock import UvLockHookEvent

# Pattern: Resolved N packages in Xms
RESOLVED_PATTERN = re.compile(r'Resolved\s+(?P<packages>\d+)\s+packages?\s+in\s+(?P<time>\d+)ms')


def run(staged_files: list[str], branch: str, project: str) -> UvLockHookEvent:
    """Run uv lock --check, return fully-typed event."""
    start_time = time.perf_counter()

    # uv-lock only checks if pyproject.toml or uv.lock are staged
    lock_files = [f for f in staged_files if f in ('pyproject.toml', 'uv.lock')]

    if not lock_files:
        return UvLockHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            packages_resolved=None,
            resolution_time_ms=None,
            files_checked=[],
            duration_seconds=0.0,
        )

    result = subprocess.run(  # nosec B603 B607
        ['uv', 'lock', '--check'],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time
    packages, time_ms = _parse_uv_lock_output(result.stdout + result.stderr)

    return UvLockHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        packages_resolved=packages,
        resolution_time_ms=time_ms,
        files_checked=lock_files,
        duration_seconds=round(duration, 3),
    )


def _parse_uv_lock_output(output: str) -> tuple[int | None, int | None]:
    """Parse uv lock output for resolution stats."""
    match = RESOLVED_PATTERN.search(output)
    if match:
        return int(match.group('packages')), int(match.group('time'))
    return None, None
