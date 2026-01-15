"""Bandit hook runner - captures ALL bandit output with full issue details."""

from __future__ import annotations

import json
import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.bandit import BanditCWE
from stats.schemas.hooks.bandit import BanditHookEvent
from stats.schemas.hooks.bandit import BanditIssue
from stats.schemas.hooks.bandit import BanditMetrics


def run(staged_files: list[str], branch: str, project: str) -> BanditHookEvent:
    """Run bandit on staged files, return fully-typed event.

    Args:
        staged_files: List of file paths to check
        branch: Current git branch
        project: Project name

    Returns:
        BanditHookEvent with full issue details
    """
    start_time = time.perf_counter()

    # Filter to only Python files
    python_files = [f for f in staged_files if f.endswith('.py')]

    if not python_files:
        return BanditHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            issues=[],
            metrics=BanditMetrics(),
            files_checked=[],
            duration_seconds=0.0,
        )

    result = subprocess.run(  # nosec B603 B607
        ['bandit', '-c', 'pyproject.toml', '-f', 'json', '-q', *python_files],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time

    # Parse bandit JSON output
    raw_output: dict = {}
    if result.stdout.strip():
        try:
            raw_output = json.loads(result.stdout)
        except json.JSONDecodeError:
            raw_output = {}

    issues = [_parse_issue(issue) for issue in raw_output.get('results', [])]
    metrics = _parse_metrics(raw_output.get('metrics', {}).get('_totals', {}))

    return BanditHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        issues=issues,
        metrics=metrics,
        files_checked=python_files,
        duration_seconds=round(duration, 3),
    )


def _parse_issue(issue: dict) -> BanditIssue:
    """Parse a single bandit issue from JSON."""
    cwe_data = issue.get('issue_cwe')
    cwe = BanditCWE(id=cwe_data['id'], link=cwe_data['link']) if cwe_data else None

    return BanditIssue(
        code=issue['code'],
        col_offset=issue['col_offset'],
        end_col_offset=issue['end_col_offset'],
        filename=issue['filename'],
        issue_confidence=issue['issue_confidence'],
        issue_cwe=cwe,
        issue_severity=issue['issue_severity'],
        issue_text=issue['issue_text'],
        line_number=issue['line_number'],
        line_range=issue['line_range'],
        more_info=issue['more_info'],
        test_id=issue['test_id'],
        test_name=issue['test_name'],
    )


def _parse_metrics(totals: dict) -> BanditMetrics:
    """Parse bandit metrics from JSON."""
    return BanditMetrics(
        confidence_high=totals.get('CONFIDENCE.HIGH', 0),
        confidence_medium=totals.get('CONFIDENCE.MEDIUM', 0),
        confidence_low=totals.get('CONFIDENCE.LOW', 0),
        confidence_undefined=totals.get('CONFIDENCE.UNDEFINED', 0),
        severity_high=totals.get('SEVERITY.HIGH', 0),
        severity_medium=totals.get('SEVERITY.MEDIUM', 0),
        severity_low=totals.get('SEVERITY.LOW', 0),
        severity_undefined=totals.get('SEVERITY.UNDEFINED', 0),
        loc=totals.get('loc', 0),
        nosec=totals.get('nosec', 0),
        skipped_tests=totals.get('skipped_tests', 0),
    )
