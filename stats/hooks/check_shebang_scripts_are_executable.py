"""Check-shebang-scripts-are-executable hook runner - detects shebang scripts without execute permission."""

from __future__ import annotations

import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.file_format import CheckShebangExecutableHookEvent


def run(staged_files: list[str], branch: str, project: str) -> CheckShebangExecutableHookEvent:
    """Run check-shebang-scripts-are-executable on staged files, return fully-typed event.

    Args:
        staged_files: List of file paths to check
        branch: Current git branch
        project: Project name

    Returns:
        CheckShebangExecutableHookEvent with files that have shebangs but aren't executable
    """
    start_time = time.perf_counter()

    if not staged_files:
        return CheckShebangExecutableHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            files_not_executable=[],
            files_checked=[],
            duration_seconds=0.0,
        )

    result = subprocess.run(  # nosec B603 B607
        ['uvx', '--from', 'pre-commit-hooks', 'check-shebang-scripts-are-executable', *staged_files],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time
    files_not_executable = _parse_output(result.stdout + result.stderr)

    return CheckShebangExecutableHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        files_not_executable=files_not_executable,
        files_checked=staged_files,
        duration_seconds=round(duration, 3),
    )


def _parse_output(output: str) -> list[str]:
    """Parse check-shebang-scripts-are-executable output for failing file paths.

    The tool outputs 3 lines per issue: the file path with error message,
    then two help lines starting with 'If'. Only extract the file path
    from the error lines.
    """
    files: list[str] = []

    for line in output.split('\n'):
        line = line.strip()
        if not line or line.startswith('If '):
            continue
        path = line.split(': ')[0] if ': ' in line else line
        files.append(path)

    return files
