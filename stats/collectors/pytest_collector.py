"""Pytest collector runner - reads pytest-json-report output."""

from __future__ import annotations

import json
from datetime import UTC
from datetime import datetime
from pathlib import Path

from stats.schemas.collectors.pytest_collector import PytestCollectEvent
from stats.schemas.collectors.pytest_collector import PytestPhase
from stats.schemas.collectors.pytest_collector import PytestSummary
from stats.schemas.collectors.pytest_collector import PytestTest


def run(branch: str, project: str, json_path: str) -> PytestCollectEvent | None:
    """Read pytest-json-report output and return fully-typed event.

    Args:
        branch: Current git branch
        project: Project name
        json_path: Path to pytest-json-report output file

    Returns:
        PytestCollectEvent with full test results, or None if file not found
    """
    path = Path(json_path)
    if not path.exists():
        return None

    with path.open() as f:
        raw_data = json.load(f)

    summary = _parse_summary(raw_data.get('summary', {}))
    tests = [_parse_test(t) for t in raw_data.get('tests', [])]

    return PytestCollectEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        summary=summary,
        tests=tests,
        duration_seconds=raw_data.get('duration', 0.0),
        exit_code=raw_data.get('exitcode', 0),
    )


def _parse_summary(summary_data: dict) -> PytestSummary:
    """Parse summary section from pytest-json-report."""
    return PytestSummary(
        passed=summary_data.get('passed', 0),
        failed=summary_data.get('failed', 0),
        skipped=summary_data.get('skipped', 0),
        error=summary_data.get('error', 0),
        total=summary_data.get('total', 0),
        collected=summary_data.get('collected', 0),
    )


def _parse_phase(phase_data: dict | None) -> PytestPhase | None:
    """Parse a test phase (setup/call/teardown)."""
    if not phase_data:
        return None
    return PytestPhase(
        outcome=phase_data.get('outcome', 'passed'),
        duration=phase_data.get('duration', 0.0),
        longrepr=phase_data.get('longrepr'),
    )


def _parse_test(test_data: dict) -> PytestTest:
    """Parse a single test result."""
    return PytestTest(
        nodeid=test_data['nodeid'],
        outcome=test_data.get('outcome', 'passed'),
        duration=test_data.get('duration', 0.0),
        setup=_parse_phase(test_data.get('setup')),
        call=_parse_phase(test_data.get('call')),
        teardown=_parse_phase(test_data.get('teardown')),
    )
