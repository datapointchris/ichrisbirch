"""Validate-html hook runner - captures HTML validation issues."""

from __future__ import annotations

import re
import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.project import HtmlValidationIssue
from stats.schemas.hooks.project import ValidateHtmlHookEvent

# Pattern: ERROR: file.html:line: message (line number is optional)
ISSUE_PATTERN = re.compile(r'^(ERROR|WARNING|INFO):\s+(.+?):(\d+)?:\s*(.+)$')


def run(staged_files: list[str], branch: str, project: str) -> ValidateHtmlHookEvent:
    """Run validate-html on staged HTML files, return fully-typed event."""
    start_time = time.perf_counter()

    html_files = [f for f in staged_files if f.endswith('.html')]

    if not html_files:
        return ValidateHtmlHookEvent(
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
        ['uv', 'run', 'python', 'scripts/pre_commit_validations/validate_html.py', *html_files],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time
    issues = _parse_validation_output(result.stdout + result.stderr)

    return ValidateHtmlHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        issues=issues,
        files_checked=html_files,
        duration_seconds=round(duration, 3),
    )


def _parse_validation_output(output: str) -> list[HtmlValidationIssue]:
    """Parse validation output into structured issues."""
    issues: list[HtmlValidationIssue] = []

    for line in output.split('\n'):
        line = line.strip()
        match = ISSUE_PATTERN.match(line)
        if match:
            level, file_path, line_num, message = match.groups()
            issues.append(
                HtmlValidationIssue(
                    file=file_path,
                    line=int(line_num) if line_num else None,
                    message=message,
                    level=level,
                )
            )

    return issues
