"""Mypy hook runner - captures all mypy errors."""

from __future__ import annotations

import re
import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.mypy import MypyError
from stats.schemas.hooks.mypy import MypyHookEvent

# Pattern to match mypy output lines
# Format: /path/file.py:line:column: severity: message  [code]
# Or:     /path/file.py:line: severity: message  [code]
MYPY_LINE_PATTERN = re.compile(
    r'^(?P<filename>.+?):(?P<line>\d+)(?::(?P<column>\d+))?: '
    r'(?P<severity>error|warning|note): (?P<message>.+?)'
    r'(?:\s+\[(?P<code>[\w-]+)\])?$'
)


def run(staged_files: list[str], branch: str, project: str) -> MypyHookEvent:
    """Run mypy on staged files, return fully-typed event.

    Args:
        staged_files: List of file paths to check
        branch: Current git branch
        project: Project name

    Returns:
        MypyHookEvent with full error details
    """
    start_time = time.perf_counter()

    # Filter to only Python files
    python_files = [f for f in staged_files if f.endswith('.py')]

    if not python_files:
        return MypyHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            errors=[],
            files_checked=[],
            duration_seconds=0.0,
        )

    result = subprocess.run(  # nosec B603 B607
        ['mypy', '--show-error-codes', '--no-error-summary', *python_files],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time

    # Parse mypy output
    errors = _parse_mypy_output(result.stdout + result.stderr)

    return MypyHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        errors=errors,
        files_checked=python_files,
        duration_seconds=round(duration, 3),
    )


def _parse_mypy_output(output: str) -> list[MypyError]:
    """Parse mypy output into structured errors."""
    errors: list[MypyError] = []

    for line in output.split('\n'):
        line = line.strip()
        if not line:
            continue

        match = MYPY_LINE_PATTERN.match(line)
        if match:
            groups = match.groupdict()
            severity = groups['severity']
            # Only capture actual errors, not notes
            if severity in ('error', 'warning'):
                errors.append(
                    MypyError(
                        filename=groups['filename'],
                        line=int(groups['line']),
                        column=int(groups['column']) if groups['column'] else None,
                        severity=severity,  # type: ignore[arg-type]
                        message=groups['message'],
                        code=groups['code'],
                    )
                )

    return errors
