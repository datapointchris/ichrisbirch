"""Check-yaml hook runner - captures YAML validation issues."""

from __future__ import annotations

import re
import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.file_format import CheckYamlHookEvent
from stats.schemas.hooks.file_format import FileFormatIssue

# Pattern to match YAML error location: in "filename", line N, column N
YAML_LOCATION_PATTERN = re.compile(r'in "(?P<path>.+?)", line (?P<line>\d+), column (?P<column>\d+)')


def run(staged_files: list[str], branch: str, project: str) -> CheckYamlHookEvent:
    """Run check-yaml on staged files, return fully-typed event."""
    start_time = time.perf_counter()

    if not staged_files:
        return CheckYamlHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            issues=[],
            files_checked=[],
            duration_seconds=0.0,
        )

    # Filter to only YAML files
    yaml_files = [f for f in staged_files if f.endswith(('.yml', '.yaml'))]

    if not yaml_files:
        return CheckYamlHookEvent(
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
        ['uvx', '--from', 'pre-commit-hooks', 'check-yaml', *yaml_files],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time
    issues = _parse_check_yaml_output(result.stdout + result.stderr)

    return CheckYamlHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        issues=issues,
        files_checked=yaml_files,
        duration_seconds=round(duration, 3),
    )


def _parse_check_yaml_output(output: str) -> list[FileFormatIssue]:
    """Parse check-yaml output into structured issues.

    Output format is multi-line:
    error message line
      in "filepath", line N, column N
    """
    issues: list[FileFormatIssue] = []
    lines = output.split('\n')
    current_message_lines: list[str] = []

    for line in lines:
        location_match = YAML_LOCATION_PATTERN.search(line)
        if location_match:
            # Found location line, create issue with accumulated message
            message = ' '.join(current_message_lines).strip()
            if message:
                issues.append(
                    FileFormatIssue(
                        path=location_match.group('path'),
                        line=int(location_match.group('line')),
                        column=int(location_match.group('column')),
                        message=message,
                    )
                )
            current_message_lines = []
        elif line.strip() and not line.startswith('  in '):
            current_message_lines.append(line.strip())

    return issues
