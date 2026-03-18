"""SASS compile hook runner - captures SCSS compilation results."""

from __future__ import annotations

import filecmp
import re
import subprocess  # nosec B404
import tempfile
import time
from datetime import UTC
from datetime import datetime
from pathlib import Path

from stats.schemas.hooks.sass import SassError
from stats.schemas.hooks.sass import SassHookEvent

# Paths matching .pre-commit-config.yaml:
#   sass ichrisbirch/app/static/sass/main.scss:ichrisbirch/app/static/css/main.css
SASS_SOURCE = 'ichrisbirch/app/static/sass/main.scss'
CSS_OUTPUT = 'ichrisbirch/app/static/css/main.css'

# Pattern to extract file location from SASS error output
# Format: "  path/to/file.scss 3:15  root stylesheet"
LOCATION_PATTERN = re.compile(r'^\s+(.+\.scss)\s+(\d+):(\d+)')


def run(staged_files: list[str], branch: str, project: str) -> SassHookEvent:
    """Run SASS compilation on staged SCSS files, return fully-typed event.

    Compiles to a temp file and compares against the committed CSS to detect
    both syntax errors AND stale CSS (matching the real pre-commit hook behavior).
    """
    start_time = time.perf_counter()

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

    # Compile to a temp file so we can compare without modifying the working tree
    with tempfile.NamedTemporaryFile(suffix='.css', delete=True) as tmp:
        tmp_path = tmp.name

    result = subprocess.run(  # nosec B603 B607
        ['sass', f'{SASS_SOURCE}:{tmp_path}'],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time

    # Parse syntax errors from stderr
    issues = _parse_sass_errors(result.stderr)

    # If compilation succeeded, check if output differs from committed CSS
    css_stale = False
    if result.returncode == 0 and Path(tmp_path).exists():
        if Path(CSS_OUTPUT).exists():
            css_stale = not filecmp.cmp(tmp_path, CSS_OUTPUT, shallow=False)
        else:
            css_stale = True  # CSS file doesn't exist yet

        if css_stale:
            issues.append(
                SassError(
                    message='Compiled CSS differs from committed file (run sass-compile to update)',
                    file=CSS_OUTPUT,
                    line=None,
                    column=None,
                )
            )

        # Clean up temp file
        Path(tmp_path).unlink(missing_ok=True)

    failed = result.returncode != 0 or css_stale

    return SassHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='failed' if failed else 'passed',
        exit_code=result.returncode if result.returncode != 0 else (1 if css_stale else 0),
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
