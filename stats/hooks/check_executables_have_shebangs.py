"""Check-executables-have-shebangs hook runner - detects executable files missing shebangs."""

from __future__ import annotations

import os
import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.file_format import CheckExecutablesShebangsHookEvent


def run(staged_files: list[str], branch: str, project: str) -> CheckExecutablesShebangsHookEvent:
    """Run check-executables-have-shebangs on staged files, return fully-typed event.

    Pre-commit only passes files with `types: [executable]` to this tool.
    The tool itself doesn't check permissions — it assumes it only receives
    executable files. We must replicate that filter here.

    Args:
        staged_files: List of file paths to check
        branch: Current git branch
        project: Project name

    Returns:
        CheckExecutablesShebangsHookEvent with files missing shebangs
    """
    start_time = time.perf_counter()

    # Pre-commit filters to types: [executable] — only pass executable files
    executable_files = [f for f in staged_files if os.access(f, os.X_OK)]

    if not executable_files:
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
        ['uvx', '--from', 'pre-commit-hooks', 'check-executables-have-shebangs', *executable_files],
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
        files_checked=executable_files,
        duration_seconds=round(duration, 3),
    )


def _parse_output(output: str) -> list[str]:
    """Parse check-executables-have-shebangs output for failing file paths.

    The tool outputs 3 lines per issue: the file path with error message,
    then two help lines starting with 'If'. Only extract the file path
    from the error lines.
    """
    files: list[str] = []

    for line in output.split('\n'):
        line = line.strip()
        if not line or line.startswith('If '):
            continue
        # Extract file path from "path: marked executable but has no..."
        path = line.split(': ')[0] if ': ' in line else line
        files.append(path)

    return files
