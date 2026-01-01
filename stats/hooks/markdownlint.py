"""Markdownlint hook runner - captures markdown linting issues."""

from __future__ import annotations

import json
import subprocess  # nosec B404
import time
from contextlib import suppress
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.markdownlint import MarkdownlintHookEvent
from stats.schemas.hooks.markdownlint import MarkdownlintIssue


def run(staged_files: list[str], branch: str, project: str) -> MarkdownlintHookEvent:
    """Run markdownlint on staged files, return fully-typed event.

    Args:
        staged_files: List of file paths to check
        branch: Current git branch
        project: Project name

    Returns:
        MarkdownlintHookEvent with full issue details
    """
    start_time = time.perf_counter()

    if not staged_files:
        return MarkdownlintHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            issues=[],
            files_checked=[],
            duration_seconds=0.0,
        )

    # Filter to only markdown files
    markdown_files = [f for f in staged_files if f.endswith('.md')]

    if not markdown_files:
        return MarkdownlintHookEvent(
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
        ['markdownlint', '--json', *markdown_files],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time

    # Parse markdownlint JSON output
    issues = _parse_markdownlint_output(result.stdout)

    return MarkdownlintHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        issues=issues,
        files_checked=markdown_files,
        duration_seconds=round(duration, 3),
    )


def _parse_markdownlint_output(output: str) -> list[MarkdownlintIssue]:
    """Parse markdownlint JSON output into structured issues."""
    if not output.strip():
        return []

    issues: list[MarkdownlintIssue] = []

    with suppress(json.JSONDecodeError):
        data = json.loads(output)
        for item in data:
            issues.append(
                MarkdownlintIssue(
                    file_name=item.get('fileName', ''),
                    line_number=item.get('lineNumber', 0),
                    rule_names=item.get('ruleNames', []),
                    rule_description=item.get('ruleDescription', ''),
                    error_detail=item.get('errorDetail'),
                    error_context=item.get('errorContext'),
                    severity=item.get('severity', 'error'),
                )
            )

    return issues
