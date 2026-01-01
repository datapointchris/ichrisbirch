"""Ruff hook runner - captures ALL ruff output with full issue details."""

from __future__ import annotations

import json
import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.ruff import RuffEdit
from stats.schemas.hooks.ruff import RuffFix
from stats.schemas.hooks.ruff import RuffHookEvent
from stats.schemas.hooks.ruff import RuffIssue
from stats.schemas.hooks.ruff import RuffLocation


def run(staged_files: list[str], branch: str, project: str) -> RuffHookEvent:
    """Run ruff on staged files, return fully-typed event.

    Args:
        staged_files: List of file paths to check
        branch: Current git branch
        project: Project name

    Returns:
        RuffHookEvent with full issue details
    """
    start_time = time.perf_counter()

    # Filter to only Python files
    python_files = [f for f in staged_files if f.endswith('.py')]

    if not python_files:
        return RuffHookEvent(
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
        ['ruff', 'check', '--output-format=json', *python_files],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time

    # Parse full ruff output - capture EVERYTHING
    raw_issues: list[dict] = []
    if result.stdout.strip():
        try:
            raw_issues = json.loads(result.stdout)
        except json.JSONDecodeError:
            raw_issues = []

    issues = [_parse_issue(issue) for issue in raw_issues]

    return RuffHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        issues=issues,
        files_checked=python_files,
        duration_seconds=round(duration, 3),
    )


def _parse_issue(issue: dict) -> RuffIssue:
    """Parse a single ruff issue from JSON."""
    return RuffIssue(
        code=issue['code'],
        message=issue['message'],
        filename=issue['filename'],
        location=RuffLocation(
            column=issue['location']['column'],
            row=issue['location']['row'],
        ),
        end_location=RuffLocation(
            column=issue['end_location']['column'],
            row=issue['end_location']['row'],
        ),
        fix=_parse_fix(issue['fix']) if issue.get('fix') else None,
        noqa_row=issue.get('noqa_row'),
        url=issue.get('url'),
        cell=issue.get('cell'),
    )


def _parse_fix(fix_data: dict) -> RuffFix:
    """Parse ruff fix information."""
    edits = [
        RuffEdit(
            content=edit['content'],
            location=RuffLocation(
                column=edit['location']['column'],
                row=edit['location']['row'],
            ),
            end_location=RuffLocation(
                column=edit['end_location']['column'],
                row=edit['end_location']['row'],
            ),
        )
        for edit in fix_data.get('edits', [])
    ]
    return RuffFix(
        applicability=fix_data['applicability'],
        edits=edits,
        message=fix_data.get('message'),
    )
