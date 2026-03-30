"""Emit test events from JSON reports written by pre-commit test hooks.

Called inline by pre-commit test hooks after tests run, so that test data
is captured even when pre-commit fails (no post-commit to collect later).

Usage:
    uv run python -m stats.collect_report pytest
    uv run python -m stats.collect_report vitest
    uv run python -m stats.collect_report playwright
"""

from __future__ import annotations

import subprocess  # nosec B404
import sys

from stats.config import load_config
from stats.emit import emit_event


def get_branch() -> str:
    """Get current git branch."""
    result = subprocess.run(  # nosec B603 B607
        ['git', 'branch', '--show-current'],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() or 'HEAD'


def _collect_pytest(branch: str, project: str, collect_config: dict) -> object | None:
    from stats.collectors.pytest_collector import run

    json_path = collect_config.get('pytest_json_path', '/tmp/ichrisbirch-pytest-report.json')  # nosec B108
    return run(branch, project, json_path)


def _collect_vitest(branch: str, project: str, collect_config: dict) -> object | None:
    from stats.collectors.vitest_collector import run

    json_path = collect_config.get('vitest_json_path', '/tmp/ichrisbirch-vitest-report.json')  # nosec B108
    return run(branch, project, json_path)


def _collect_playwright(branch: str, project: str, collect_config: dict) -> object | None:
    from stats.collectors.playwright_collector import run

    json_path = collect_config.get('playwright_json_path', '/tmp/ichrisbirch-playwright-report.json')  # nosec B108
    return run(branch, project, json_path)


COLLECTORS = {
    'pytest': _collect_pytest,
    'vitest': _collect_vitest,
    'playwright': _collect_playwright,
}


def main() -> int:
    """Collect a test report and emit it as an event."""
    if len(sys.argv) < 2:
        print('Usage: python -m stats.collect_report <pytest|vitest|playwright>')
        return 1

    report_type = sys.argv[1]

    if report_type not in COLLECTORS:
        print(f'Unknown report type: {report_type}')
        return 1

    config = load_config()
    project = config['project']
    events_path = config['events_path']
    branch = get_branch()
    collect_config = config.get('collect', {})

    event = COLLECTORS[report_type](branch, project, collect_config)

    if event is not None:
        emit_event(event, events_path)  # type: ignore[arg-type]

    return 0


if __name__ == '__main__':
    sys.exit(main())
