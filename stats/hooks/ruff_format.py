"""Ruff format hook runner - captures files that would be reformatted."""

from __future__ import annotations

import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.ruff import RuffFormatHookEvent


def run(staged_files: list[str], branch: str, project: str) -> RuffFormatHookEvent:
    """Run ruff format --check on staged files, return fully-typed event.

    Args:
        staged_files: List of file paths to check
        branch: Current git branch
        project: Project name

    Returns:
        RuffFormatHookEvent with files that would be reformatted
    """
    start_time = time.perf_counter()

    python_files = [f for f in staged_files if f.endswith('.py')]

    if not python_files:
        return RuffFormatHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            files_reformatted=[],
            files_checked=[],
            duration_seconds=0.0,
        )

    result = subprocess.run(  # nosec B603 B607
        ['ruff', 'format', '--check', *python_files],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time
    files_reformatted = _parse_format_output(result.stdout + result.stderr)

    return RuffFormatHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        files_reformatted=files_reformatted,
        files_checked=python_files,
        duration_seconds=round(duration, 3),
    )


def _parse_format_output(output: str) -> list[str]:
    """Parse ruff format --check output for files that would be reformatted.

    Output lines look like: "Would reformat: path/to/file.py"
    """
    reformatted: list[str] = []

    for line in output.split('\n'):
        line = line.strip()
        if line.startswith('Would reformat:'):
            path = line.removeprefix('Would reformat:').strip()
            if path:
                reformatted.append(path)

    return reformatted
