"""Check-toml hook runner - captures TOML validation issues."""

from __future__ import annotations

import re
import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.file_format import CheckTomlHookEvent
from stats.schemas.hooks.file_format import FileFormatIssue

# Pattern: filepath: error message (at line N, column N)
TOML_ERROR_PATTERN = re.compile(r'^(?P<path>.+?): (?P<message>.+?) \(at line (?P<line>\d+), column (?P<column>\d+)\)$')


def run(staged_files: list[str], branch: str, project: str) -> CheckTomlHookEvent:
    """Run check-toml on staged files, return fully-typed event."""
    start_time = time.perf_counter()

    if not staged_files:
        return CheckTomlHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            issues=[],
            files_checked=[],
            duration_seconds=0.0,
        )

    # Filter to only TOML files
    toml_files = [f for f in staged_files if f.endswith('.toml')]

    if not toml_files:
        return CheckTomlHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            issues=[],
            files_checked=[],
            duration_seconds=0.0,
        )

    result = subprocess.run(  # nosec B603 B607
        ['uvx', '--from', 'pre-commit-hooks', 'check-toml', *toml_files],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time
    issues = _parse_check_toml_output(result.stdout + result.stderr)

    return CheckTomlHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        issues=issues,
        files_checked=toml_files,
        duration_seconds=round(duration, 3),
    )


def _parse_check_toml_output(output: str) -> list[FileFormatIssue]:
    """Parse check-toml output into structured issues."""
    issues: list[FileFormatIssue] = []

    for line in output.split('\n'):
        line = line.strip()
        if not line:
            continue

        match = TOML_ERROR_PATTERN.match(line)
        if match:
            issues.append(
                FileFormatIssue(
                    path=match.group('path'),
                    line=int(match.group('line')),
                    column=int(match.group('column')),
                    message=match.group('message'),
                )
            )

    return issues
