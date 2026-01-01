"""Trailing-whitespace hook runner - captures whitespace fixes."""

from __future__ import annotations

import re
import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.fixers import TrailingWhitespaceHookEvent

# Pattern: Fixing filepath
FIXING_PATTERN = re.compile(r'^Fixing\s+(.+)$')


def run(staged_files: list[str], branch: str, project: str) -> TrailingWhitespaceHookEvent:
    """Run trailing-whitespace-fixer on staged files, return fully-typed event."""
    start_time = time.perf_counter()

    if not staged_files:
        return TrailingWhitespaceHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            fixed_files=[],
            files_checked=[],
            duration_seconds=0.0,
        )

    result = subprocess.run(  # nosec B603 B607
        ['uvx', '--from', 'pre-commit-hooks', 'trailing-whitespace-fixer', *staged_files],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time
    fixed_files = _parse_fixer_output(result.stdout + result.stderr)

    return TrailingWhitespaceHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        fixed_files=fixed_files,
        files_checked=staged_files,
        duration_seconds=round(duration, 3),
    )


def _parse_fixer_output(output: str) -> list[str]:
    """Parse fixer output for fixed files."""
    fixed: list[str] = []

    for line in output.split('\n'):
        line = line.strip()
        match = FIXING_PATTERN.match(line)
        if match:
            fixed.append(match.group(1))

    return fixed
