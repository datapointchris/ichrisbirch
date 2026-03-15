"""Vitest collector runner - reads vitest JSON reporter output."""

from __future__ import annotations

import json
from datetime import UTC
from datetime import datetime
from pathlib import Path

from stats.schemas.collectors.vitest_collector import VitestCollectEvent
from stats.schemas.collectors.vitest_collector import VitestSummary
from stats.schemas.collectors.vitest_collector import VitestTest


def run(branch: str, project: str, json_path: str) -> VitestCollectEvent | None:
    """Read vitest JSON reporter output and return fully-typed event.

    Args:
        branch: Current git branch
        project: Project name
        json_path: Path to vitest JSON reporter output file

    Returns:
        VitestCollectEvent with full test results, or None if file not found
    """
    path = Path(json_path)
    if not path.exists():
        return None

    with path.open() as f:
        raw_data = json.load(f)

    tests = _parse_tests(raw_data.get('testResults', []))
    summary = VitestSummary(
        passed=raw_data.get('numPassedTests', 0),
        failed=raw_data.get('numFailedTests', 0),
        skipped=raw_data.get('numSkippedTests', 0),
        total=raw_data.get('numTotalTests', 0),
    )

    duration_seconds = sum(t.duration for t in tests)

    return VitestCollectEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        summary=summary,
        tests=tests,
        duration_seconds=duration_seconds,
        exit_code=0 if raw_data.get('success', False) else 1,
    )


def _parse_tests(test_results: list[dict]) -> list[VitestTest]:
    """Flatten testResults → assertionResults into VitestTest objects."""
    tests = []
    for suite in test_results:
        suite_name = suite.get('name', '')
        for assertion in suite.get('assertionResults', []):
            duration_ms = assertion.get('duration', 0)
            tests.append(
                VitestTest(
                    name=assertion.get('fullName', ''),
                    suite=suite_name,
                    outcome=assertion.get('status', 'passed'),
                    duration=duration_ms / 1000.0,
                )
            )
    return tests
