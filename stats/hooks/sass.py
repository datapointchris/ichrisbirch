"""SASS compile hook runner - captures SCSS compilation results."""

from __future__ import annotations

import re
import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.sass import SassError
from stats.schemas.hooks.sass import SassHookEvent

# SASS source path (matching .pre-commit-config.yaml)
SASS_SOURCE = 'ichrisbirch/app/static/sass/main.scss'

# Pattern to extract file location from SASS error output
# Format: "  path/to/file.scss 3:15  root stylesheet"
LOCATION_PATTERN = re.compile(r'^\s+(.+\.scss)\s+(\d+):(\d+)')


def run(staged_files: list[str], branch: str, project: str) -> SassHookEvent:
    """Run SASS compilation on staged SCSS files, return fully-typed event.

    Args:
        staged_files: List of file paths to check
        branch: Current git branch
        project: Project name

    Returns:
        SassHookEvent with compilation results
    """
    start_time = time.perf_counter()

    # Filter to only SCSS files
    scss_files = [f for f in staged_files if f.endswith('.scss')]

    if not scss_files:
        return SassHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            issues=[],
            files_checked=[],
            duration_seconds=0.0,
        )

    # Run sass compilation to stdout only (no file modification)
    # This checks for errors without interfering with the actual sass-compile hook
    result = subprocess.run(  # nosec B603 B607
        ['sass', SASS_SOURCE],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time

    # Parse any errors from stderr
    issues = _parse_sass_errors(result.stderr)

    return SassHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        issues=issues,
        files_checked=scss_files,
        duration_seconds=round(duration, 3),
    )


def _parse_sass_errors(output: str) -> list[SassError]:
    """Parse SASS error output into structured errors.

    SASS error output looks like:
        Error: expected "{".
           ╷
         3 │ .invalid-syntax
           │               ^
           ╵
          ichrisbirch/app/static/sass/main.scss 3:15  root stylesheet
    """
    issues: list[SassError] = []

    if not output.strip():
        return issues

    # Split by "Error:" to handle multiple errors
    error_blocks = output.split('Error:')

    for block in error_blocks:
        block = block.strip()
        if not block:
            continue

        # First line is the error message
        lines = block.split('\n')
        message = f'Error: {lines[0].strip()}'

        # Look for file location in remaining lines
        file_path = None
        line_num = None
        column = None

        for line in lines[1:]:
            match = LOCATION_PATTERN.match(line)
            if match:
                file_path = match.group(1)
                line_num = int(match.group(2))
                column = int(match.group(3))
                break

        issues.append(
            SassError(
                message=message,
                file=file_path,
                line=line_num,
                column=column,
            )
        )

    return issues
