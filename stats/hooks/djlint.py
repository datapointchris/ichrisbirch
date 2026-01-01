"""Djlint hook runner - captures Jinja/HTML template linting issues."""

from __future__ import annotations

import re
import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.djlint import DjlintHookEvent
from stats.schemas.hooks.djlint import DjlintIssue

# Pattern to match djlint issue lines
# Format: H005 2:0 Html tag should have lang attribute. <html> <head>
ISSUE_PATTERN = re.compile(r'^(?P<code>[A-Z]\d+)\s+(?P<line>\d+):(?P<column>\d+)\s+(?P<message>.+)$')

# Pattern to detect separator lines (all dashes)
SEPARATOR_PATTERN = re.compile(r'^─+$')


def run(staged_files: list[str], branch: str, project: str) -> DjlintHookEvent:
    """Run djlint on staged files, return fully-typed event.

    Args:
        staged_files: List of file paths to check
        branch: Current git branch
        project: Project name

    Returns:
        DjlintHookEvent with full issue details
    """
    start_time = time.perf_counter()

    if not staged_files:
        return DjlintHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            issues=[],
            files_checked=[],
            duration_seconds=0.0,
        )

    # Filter to only HTML/Jinja template files
    template_extensions = ('.html', '.jinja', '.jinja2')
    template_files = [f for f in staged_files if f.endswith(template_extensions)]

    if not template_files:
        return DjlintHookEvent(
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
        ['djlint', '--profile=jinja', '--lint', *template_files],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time

    # Parse djlint output
    issues = _parse_djlint_output(result.stdout)

    return DjlintHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        issues=issues,
        files_checked=template_files,
        duration_seconds=round(duration, 3),
    )


def _parse_djlint_output(output: str) -> list[DjlintIssue]:
    """Parse djlint output into structured issues.

    Djlint output format:
    {file_path}
    ───────────────────────────────────────────────────────────────────────────────
    H005 2:0 Html tag should have lang attribute. <html> <head>
    H006 9:0 Img tag should have height and width attributes. <img src="test.jpg">
    """
    issues: list[DjlintIssue] = []
    current_file: str | None = None

    for line in output.split('\n'):
        line = line.strip()
        if not line:
            continue

        # Skip progress lines and summary lines
        if 'Linting' in line or 'Linted' in line or 'files' in line:
            continue

        # Skip separator lines
        if SEPARATOR_PATTERN.match(line):
            continue

        # Check if this is an issue line
        issue_match = ISSUE_PATTERN.match(line)
        if issue_match:
            if current_file:
                groups = issue_match.groupdict()
                issues.append(
                    DjlintIssue(
                        path=current_file,
                        line=int(groups['line']),
                        column=int(groups['column']),
                        code=groups['code'],
                        message=groups['message'].rstrip(),
                    )
                )
        else:
            # This might be a file path
            # File paths don't start with a code pattern and don't contain only dashes
            if line and not line.startswith(('H', 'D', 'J', 'T', 'W', 'E')):
                current_file = line

    return issues
