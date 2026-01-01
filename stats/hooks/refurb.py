"""Refurb hook runner - captures Python improvement suggestions."""

from __future__ import annotations

import re
import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.refurb import RefurbHookEvent
from stats.schemas.hooks.refurb import RefurbIssue

# Pattern to match refurb output lines
# Format: path:line:column [CODE]: message
REFURB_LINE_PATTERN = re.compile(r'^(?P<path>.+?):(?P<line>\d+):(?P<column>\d+)\s+\[(?P<code>FURB\d+)\]:\s+(?P<message>.+)$')


def run(staged_files: list[str], branch: str, project: str) -> RefurbHookEvent:
    """Run refurb on staged files, return fully-typed event.

    Args:
        staged_files: List of file paths to check
        branch: Current git branch
        project: Project name

    Returns:
        RefurbHookEvent with full issue details
    """
    start_time = time.perf_counter()

    if not staged_files:
        return RefurbHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            issues=[],
            files_checked=[],
            duration_seconds=0.0,
        )

    # Filter to only Python files
    python_files = [f for f in staged_files if f.endswith('.py')]

    if not python_files:
        return RefurbHookEvent(
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
        ['refurb', '--quiet', *python_files],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time

    # Parse refurb output
    issues = _parse_refurb_output(result.stdout + result.stderr)

    return RefurbHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        issues=issues,
        files_checked=python_files,
        duration_seconds=round(duration, 3),
    )


def _parse_refurb_output(output: str) -> list[RefurbIssue]:
    """Parse refurb output into structured issues."""
    issues: list[RefurbIssue] = []

    for line in output.split('\n'):
        line = line.strip()
        if not line:
            continue

        match = REFURB_LINE_PATTERN.match(line)
        if match:
            groups = match.groupdict()
            issues.append(
                RefurbIssue(
                    path=groups['path'],
                    line=int(groups['line']),
                    column=int(groups['column']),
                    code=groups['code'],
                    message=groups['message'],
                )
            )

    return issues
