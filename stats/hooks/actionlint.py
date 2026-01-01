"""Actionlint hook runner - captures GitHub Actions workflow linting issues."""

from __future__ import annotations

import json
import subprocess  # nosec B404
import time
from contextlib import suppress
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.actionlint import ActionlintHookEvent
from stats.schemas.hooks.actionlint import ActionlintIssue


def run(staged_files: list[str], branch: str, project: str) -> ActionlintHookEvent:
    """Run actionlint on staged files, return fully-typed event.

    Args:
        staged_files: List of file paths to check
        branch: Current git branch
        project: Project name

    Returns:
        ActionlintHookEvent with full issue details
    """
    start_time = time.perf_counter()

    if not staged_files:
        return ActionlintHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            issues=[],
            files_checked=[],
            duration_seconds=0.0,
        )

    # Filter to only GitHub workflow files (.github/workflows/*.yml or *.yaml)
    workflow_files = [f for f in staged_files if f.startswith('.github/workflows/') and f.endswith(('.yml', '.yaml'))]

    if not workflow_files:
        return ActionlintHookEvent(
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
        ['actionlint', '-format', '{{json .}}', *workflow_files],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time

    # Parse actionlint JSON output
    issues = _parse_actionlint_output(result.stdout)

    return ActionlintHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        issues=issues,
        files_checked=workflow_files,
        duration_seconds=round(duration, 3),
    )


def _parse_actionlint_output(output: str) -> list[ActionlintIssue]:
    """Parse actionlint JSON output into structured issues."""
    if not output.strip():
        return []

    issues: list[ActionlintIssue] = []

    with suppress(json.JSONDecodeError):
        data = json.loads(output)
        for item in data:
            issues.append(
                ActionlintIssue(
                    message=item.get('message', ''),
                    filepath=item.get('filepath', ''),
                    line=item.get('line', 0),
                    column=item.get('column', 0),
                    kind=item.get('kind', ''),
                    snippet=item.get('snippet'),
                )
            )

    return issues
