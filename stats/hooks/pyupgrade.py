"""Pyupgrade hook runner - captures Python syntax upgrade rewrites."""

from __future__ import annotations

import re
import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.pyupgrade import PyupgradeHookEvent

# Pattern to match pyupgrade "Rewriting" output lines
# Format: Rewriting /path/to/file.py
REWRITING_PATTERN = re.compile(r'^Rewriting\s+(.+)$')


def run(staged_files: list[str], branch: str, project: str) -> PyupgradeHookEvent:
    """Run pyupgrade on staged files, return fully-typed event.

    Args:
        staged_files: List of file paths to check
        branch: Current git branch
        project: Project name

    Returns:
        PyupgradeHookEvent with rewrite details
    """
    start_time = time.perf_counter()

    if not staged_files:
        return PyupgradeHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            rewritten_files=[],
            files_checked=[],
            duration_seconds=0.0,
        )

    # Filter to only Python files
    python_files = [f for f in staged_files if f.endswith('.py')]

    if not python_files:
        return PyupgradeHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            rewritten_files=[],
            files_checked=[],
            duration_seconds=0.0,
        )

    result = subprocess.run(  # nosec B603 B607
        ['pyupgrade', '--py312-plus', *python_files],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time

    # Parse pyupgrade output for rewritten files
    rewritten_files = _parse_pyupgrade_output(result.stdout + result.stderr)

    return PyupgradeHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        rewritten_files=rewritten_files,
        files_checked=python_files,
        duration_seconds=round(duration, 3),
    )


def _parse_pyupgrade_output(output: str) -> list[str]:
    """Parse pyupgrade output to find rewritten files."""
    rewritten: list[str] = []

    for line in output.split('\n'):
        line = line.strip()
        if not line:
            continue

        match = REWRITING_PATTERN.match(line)
        if match:
            rewritten.append(match.group(1))

    return rewritten
