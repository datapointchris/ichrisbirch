"""Codespell hook runner - captures ALL codespell output with full details."""

from __future__ import annotations

import re
import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.codespell import CodespellHookEvent
from stats.schemas.hooks.codespell import CodespellIssue

# Pattern to match codespell output lines
# Format: filename:line: word ==> correction
CODESPELL_LINE_PATTERN = re.compile(r'^(?P<filename>.+?):(?P<line>\d+):\s+(?P<word>\S+)\s+==>\s+(?P<correction>.+)$')


def run(staged_files: list[str], branch: str, project: str) -> CodespellHookEvent:
    """Run codespell on staged files, return fully-typed event.

    Args:
        staged_files: List of file paths to check
        branch: Current git branch
        project: Project name

    Returns:
        CodespellHookEvent with full issue details
    """
    start_time = time.perf_counter()

    if not staged_files:
        return CodespellHookEvent(
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
        ['codespell', *staged_files],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time

    # Parse codespell output
    issues = _parse_codespell_output(result.stdout + result.stderr)

    return CodespellHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        issues=issues,
        files_checked=staged_files,
        duration_seconds=round(duration, 3),
    )


def _parse_codespell_output(output: str) -> list[CodespellIssue]:
    """Parse codespell output into structured issues."""
    issues: list[CodespellIssue] = []

    for line in output.split('\n'):
        line = line.strip()
        if not line:
            continue

        match = CODESPELL_LINE_PATTERN.match(line)
        if match:
            groups = match.groupdict()
            issues.append(
                CodespellIssue(
                    filename=groups['filename'],
                    line=int(groups['line']),
                    word=groups['word'],
                    correction=groups['correction'],
                )
            )

    return issues
