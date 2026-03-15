"""Terraform tflint hook runner - captures lint issues from tflint JSON output."""

from __future__ import annotations

import json
import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime
from pathlib import Path

from stats.schemas.hooks.terraform import TerraformTflintHookEvent
from stats.schemas.hooks.terraform import TflintIssue


def run(staged_files: list[str], branch: str, project: str) -> TerraformTflintHookEvent:
    """Run tflint on staged .tf files, return fully-typed event.

    Runs tflint --format json in each unique directory containing staged .tf files.
    Collects all issues across directories.

    Args:
        staged_files: List of file paths to check
        branch: Current git branch
        project: Project name

    Returns:
        TerraformTflintHookEvent with lint issues
    """
    start_time = time.perf_counter()

    tf_files = [f for f in staged_files if f.endswith('.tf')]

    if not tf_files:
        return TerraformTflintHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            issues=[],
            files_checked=[],
            duration_seconds=0.0,
        )

    directories = sorted({str(Path(f).parent) for f in tf_files})

    overall_exit_code = 0
    all_issues: list[TflintIssue] = []

    for directory in directories:
        result = subprocess.run(  # nosec B603 B607
            ['tflint', '--format', 'json'],
            capture_output=True,
            text=True,
            cwd=directory,
        )
        if result.returncode != 0:
            overall_exit_code = result.returncode

        if result.stdout.strip():
            try:
                raw_output = json.loads(result.stdout)
            except json.JSONDecodeError:
                continue

            for issue in raw_output.get('issues', []):
                all_issues.append(_parse_issue(issue))

    duration = time.perf_counter() - start_time

    return TerraformTflintHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if overall_exit_code == 0 else 'failed',
        exit_code=overall_exit_code,
        issues=all_issues,
        files_checked=tf_files,
        duration_seconds=round(duration, 3),
    )


def _parse_issue(issue: dict) -> TflintIssue:
    """Parse a single tflint issue from JSON output."""
    rule_data = issue.get('rule', {})
    range_data = issue.get('range', {})
    start_data = range_data.get('start', {})

    return TflintIssue(
        rule=rule_data.get('name', ''),
        message=issue.get('message', ''),
        severity=rule_data.get('severity', ''),
        file=range_data.get('filename'),
        line=start_data.get('line'),
    )
