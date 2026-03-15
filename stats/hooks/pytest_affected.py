"""Pytest-affected hook runner - captures affected test execution metadata."""

from __future__ import annotations

import re
import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.testing import PytestAffectedHookEvent

# Patterns to extract test counts from pytest output
PASSED_PATTERN = re.compile(r'(\d+)\s+passed')
COLLECTED_PATTERN = re.compile(r'collected\s+(\d+)\s+item')


def run(staged_files: list[str], branch: str, project: str) -> PytestAffectedHookEvent:
    """Run pytest-affected on staged Python files, return fully-typed event."""
    start_time = time.perf_counter()

    py_files = [f for f in staged_files if f.endswith('.py')]

    if not py_files:
        return PytestAffectedHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='skipped',
            exit_code=0,
            tests_selected=0,
            duration_seconds=0.0,
        )

    result = subprocess.run(  # nosec B603 B607
        ['uv', 'run', 'python', 'scripts/pre_commit_validations/pytest_affected.py'],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time
    output = result.stdout + result.stderr
    tests_selected = _parse_test_count(output)

    return PytestAffectedHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        tests_selected=tests_selected,
        duration_seconds=round(duration, 3),
    )


def _parse_test_count(output: str) -> int:
    """Parse pytest output for test count.

    Looks for 'X passed' first, then falls back to 'collected X items'.
    Returns 0 if neither pattern is found.
    """
    passed_match = PASSED_PATTERN.search(output)
    if passed_match:
        return int(passed_match.group(1))

    collected_match = COLLECTED_PATTERN.search(output)
    if collected_match:
        return int(collected_match.group(1))

    return 0
