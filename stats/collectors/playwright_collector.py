"""Playwright collector runner - reads Playwright JSON reporter output."""

from __future__ import annotations

import json
from datetime import UTC
from datetime import datetime
from pathlib import Path

from stats.schemas.collectors.playwright_collector import PlaywrightCollectEvent
from stats.schemas.collectors.playwright_collector import PlaywrightSummary
from stats.schemas.collectors.playwright_collector import PlaywrightTest


def run(branch: str, project: str, json_path: str) -> PlaywrightCollectEvent | None:
    """Read Playwright JSON reporter output and return fully-typed event.

    Args:
        branch: Current git branch
        project: Project name
        json_path: Path to Playwright JSON reporter output file

    Returns:
        PlaywrightCollectEvent with test results, or None if file not found
    """
    path = Path(json_path)
    if not path.exists():
        return None

    with path.open() as f:
        raw_data = json.load(f)

    tests: list[PlaywrightTest] = []
    for suite in raw_data.get('suites', []):
        _walk_suite(suite, '', tests)

    passed = 0
    failed = 0
    skipped = 0
    for test in tests:
        if test.outcome in ('passed', 'expected'):
            passed += 1
        elif test.outcome == 'skipped':
            skipped += 1
        else:
            failed += 1

    summary = PlaywrightSummary(
        passed=passed,
        failed=failed,
        skipped=skipped,
        total=len(tests),
    )

    duration_seconds = sum(t.duration for t in tests)

    return PlaywrightCollectEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        summary=summary,
        tests=tests,
        duration_seconds=duration_seconds,
        exit_code=0 if failed == 0 else 1,
    )


def _walk_suite(suite: dict, parent_title: str, tests: list[PlaywrightTest]) -> None:
    """Recursively walk Playwright suite tree to extract test results."""
    suite_title = suite.get('title', '')
    full_title = f'{parent_title} > {suite_title}' if parent_title else suite_title

    for spec in suite.get('specs', []):
        spec_title = spec.get('title', '')
        for test in spec.get('tests', []):
            results = test.get('results', [])
            if results:
                last_result = results[-1]
                status = last_result.get('status', 'unknown')
                duration_ms = last_result.get('duration', 0)
                tests.append(
                    PlaywrightTest(
                        name=spec_title,
                        suite=full_title,
                        outcome=status,
                        duration=duration_ms / 1000.0,
                    )
                )

    for child_suite in suite.get('suites', []):
        _walk_suite(child_suite, full_title, tests)
