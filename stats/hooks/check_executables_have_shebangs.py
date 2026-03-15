"""Check-executables-have-shebangs hook runner - detects executable files missing shebangs."""

from __future__ import annotations

import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.file_format import CheckExecutablesShebangsHookEvent


def run(staged_files: list[str], branch: str, project: str) -> CheckExecutablesShebangsHookEvent:
    """Run check-executables-have-shebangs on staged files, return fully-typed event.

    Args:
        staged_files: List of file paths to check
        branch: Current git branch
        project: Project name

    Returns:
        CheckExecutablesShebangsHookEvent with files missing shebangs
    """
    start_time = time.perf_counter()

    if not staged_files:
        return CheckExecutablesShebangsHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            files_without_shebangs=[],
            files_checked=[],
            duration_seconds=0.0,
        )

    result = subprocess.run(  # nosec B603 B607
        ['uvx', '--from', 'pre-commit-hooks', 'check-executables-have-shebangs', *staged_files],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time
    files_without_shebangs = _parse_output(result.stdout + result.stderr)

    return CheckExecutablesShebangsHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        files_without_shebangs=files_without_shebangs,
        files_checked=staged_files,
        duration_seconds=round(duration, 3),
    )


def _parse_output(output: str) -> list[str]:
    """Parse check-executables-have-shebangs output for failing file paths."""
    files: list[str] = []

    for line in output.split('\n'):
        line = line.strip()
        if line:
            files.append(line)

    return files
