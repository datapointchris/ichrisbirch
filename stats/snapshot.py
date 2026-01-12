#!/usr/bin/env python
"""Generate stats snapshots from event-sourced JSONL data.

This module aggregates events from stats/events/events.jsonl into
stats_*.json snapshot files that the CLI expects.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Any

from stats.config import load_config


def parse_size_to_mb(size_str: str) -> float:
    """Convert docker size string (e.g., '3.34GB', '500MB') to MB."""
    size_str = size_str.strip().upper()
    match = re.match(r'([\d.]+)\s*(GB|MB|KB|B)', size_str)
    if not match:
        return 0.0

    value = float(match.group(1))
    unit = match.group(2)

    if unit == 'GB':
        return round(value * 1024, 1)
    elif unit == 'MB':
        return round(value, 1)
    elif unit == 'KB':
        return round(value / 1024, 1)
    return round(value / (1024 * 1024), 1)


def read_events_backwards(events_path: str, limit: int = 5000) -> list[dict]:
    """Read events from JSONL file, most recent first.

    Args:
        events_path: Path to events.jsonl file
        limit: Maximum number of events to read

    Returns:
        List of events, most recent first
    """
    path = Path(events_path)
    if not path.exists():
        return []

    events = []
    with path.open('r') as f:
        lines = f.readlines()

    for line in reversed(lines[-limit:]):
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    return events


def find_latest_commit_events(events: list[dict]) -> tuple[dict | None, list[dict], list[dict]]:
    """Find the latest commit and its associated collector/hook events.

    Events are read most-recent-first, so collector events appear BEFORE
    their associated commit event. We collect events until we find a commit,
    then return those as the associated events.

    Args:
        events: List of events (most recent first)

    Returns:
        Tuple of (commit_event, collector_events, hook_events)
    """
    commit_event = None
    collector_events = []
    hook_events = []

    for event in events:
        event_type = event.get('type', '')

        if event_type == 'commit':
            commit_event = event
            break

        if event_type.startswith('collect.'):
            collector_events.append(event)
        elif event_type.startswith('hook.'):
            hook_events.append(event)

    return commit_event, collector_events, hook_events


def build_code_section(tokei_event: dict | None) -> dict:
    """Build the 'code' section from a tokei collector event."""
    if not tokei_event:
        return {'languages': {}, 'total': {'code': 0, 'comments': 0, 'blanks': 0}}

    languages = {}
    for lang_name, lang_data in tokei_event.get('languages', {}).items():
        files = lang_data.get('files', [])
        languages[lang_name] = {
            'code': lang_data.get('code', 0),
            'comments': lang_data.get('comments', 0),
            'blanks': lang_data.get('blanks', 0),
            'files': len(files),
        }

    total = {
        'code': tokei_event.get('total_code', 0),
        'comments': tokei_event.get('total_comments', 0),
        'blanks': tokei_event.get('total_blanks', 0),
    }

    return {'languages': languages, 'total': total}


def build_tests_section(pytest_event: dict | None) -> dict:
    """Build the 'tests' section from a pytest collector event."""
    if not pytest_event:
        return {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0,
            'duration_seconds': 0,
            'slowest': [],
            'source': 'pytest-json-report',
        }

    summary = pytest_event.get('summary', {})
    tests = pytest_event.get('tests', [])

    sorted_tests = sorted(
        [t for t in tests if t.get('outcome') == 'passed'],
        key=lambda t: sum(
            (t.get('setup', {}) or {}).get('duration', 0)
            + (t.get('call', {}) or {}).get('duration', 0)
            + (t.get('teardown', {}) or {}).get('duration', 0)
            for _ in (1,)
        ),
        reverse=True,
    )

    slowest = []
    for t in sorted_tests[:10]:
        duration = (
            (t.get('setup', {}) or {}).get('duration', 0)
            + (t.get('call', {}) or {}).get('duration', 0)
            + (t.get('teardown', {}) or {}).get('duration', 0)
        )
        slowest.append(
            {
                'name': t.get('nodeid', ''),
                'duration': round(duration, 3),
                'outcome': t.get('outcome', 'unknown'),
            }
        )

    total_duration = sum(
        (t.get('setup', {}) or {}).get('duration', 0)
        + (t.get('call', {}) or {}).get('duration', 0)
        + (t.get('teardown', {}) or {}).get('duration', 0)
        for t in tests
    )

    return {
        'total': summary.get('total', 0),
        'passed': summary.get('passed', 0),
        'failed': summary.get('failed', 0),
        'skipped': summary.get('skipped', 0),
        'errors': summary.get('error', 0),
        'duration_seconds': round(total_duration, 2),
        'slowest': slowest,
        'source': 'pytest-json-report',
    }


def build_coverage_section(coverage_event: dict | None) -> dict:
    """Build the 'coverage' section from a coverage collector event.

    Note: The coverage collector doesn't run by default in post-commit
    (requires running tests first), so this may be empty.
    """
    if not coverage_event:
        return {
            'line_percent': 0,
            'covered_lines': 0,
            'missing_lines': 0,
            'excluded_lines': 0,
            'num_statements': 0,
            'source': 'coverage.py',
        }

    summary = coverage_event.get('summary', {})
    return {
        'line_percent': round(summary.get('percent_covered', 0), 2),
        'covered_lines': summary.get('covered_lines', 0),
        'missing_lines': summary.get('missing_lines', 0),
        'excluded_lines': summary.get('excluded_lines', 0),
        'num_statements': summary.get('covered_lines', 0) + summary.get('missing_lines', 0),
        'source': 'coverage.py',
    }


def build_docker_section(docker_event: dict | None) -> dict:
    """Build the 'docker' section from a docker collector event."""
    if not docker_event:
        return {'images': [], 'total_size_mb': 0, 'count': 0}

    images = []
    total_size_mb = 0.0

    for img in docker_event.get('images', []):
        size_mb = parse_size_to_mb(img.get('size', '0B'))
        total_size_mb += size_mb
        images.append(
            {
                'repository': img.get('repository', ''),
                'tag': img.get('tag', ''),
                'size_mb': size_mb,
                'created': img.get('created', ''),
                'id': img.get('image_id', ''),
            }
        )

    return {
        'images': images,
        'total_size_mb': round(total_size_mb, 1),
        'count': len(images),
    }


def build_dependencies_section(deps_event: dict | None) -> dict:
    """Build the 'dependencies' section from a dependencies collector event."""
    if not deps_event:
        return {'direct': 0, 'dev': 0, 'total': 0}

    return {
        'direct': 40,
        'dev': 0,
        'total': deps_event.get('total_count', 0),
    }


def build_quality_section(hook_events: list[dict]) -> dict:
    """Build the 'quality' section from hook events."""
    quality = {
        'ruff_issues': 0,
        'mypy_errors': 0,
        'bandit_issues': 0,
        'shellcheck_issues': 0,
        'codespell_issues': 0,
    }

    for event in hook_events:
        event_type = event.get('type', '')
        issues = event.get('issues', [])
        errors = event.get('errors', [])

        if event_type == 'hook.ruff':
            quality['ruff_issues'] = len(issues)
        elif event_type == 'hook.mypy':
            quality['mypy_errors'] = len(errors)
        elif event_type == 'hook.bandit':
            quality['bandit_issues'] = len(issues)
        elif event_type == 'hook.shellcheck':
            comments = event.get('comments', [])
            quality['shellcheck_issues'] = len(comments)
        elif event_type == 'hook.codespell':
            quality['codespell_issues'] = len(issues)

    return quality


def build_commit_section(commit_event: dict) -> dict:
    """Build the 'commit' section from a commit event."""
    return {
        'hash': commit_event.get('hash', ''),
        'short': commit_event.get('short_hash', ''),
        'author': commit_event.get('author', ''),
        'email': commit_event.get('email', ''),
        'date': commit_event.get('timestamp', ''),
        'message': commit_event.get('message', ''),
        'branch': commit_event.get('branch', ''),
        'files_changed': commit_event.get('files_changed', 0),
        'insertions': commit_event.get('insertions', 0),
        'deletions': commit_event.get('deletions', 0),
    }


def build_snapshot(
    commit_event: dict,
    collector_events: list[dict],
    hook_events: list[dict],
) -> dict[str, Any]:
    """Build a complete snapshot from events."""
    collectors_by_type = {e.get('type'): e for e in collector_events}

    snapshot = {
        'collected_at': datetime.now(UTC).isoformat(),
        'commit': build_commit_section(commit_event),
        'code': build_code_section(collectors_by_type.get('collect.tokei')),
        'tests': build_tests_section(collectors_by_type.get('collect.pytest')),
        'coverage': build_coverage_section(collectors_by_type.get('collect.coverage')),
        'docker': build_docker_section(collectors_by_type.get('collect.docker')),
        'dependencies': build_dependencies_section(collectors_by_type.get('collect.dependencies')),
        'quality': build_quality_section(hook_events),
    }

    return snapshot


def write_snapshot(snapshot: dict, output_dir: str) -> Path:
    """Write snapshot to a timestamped JSON file.

    Args:
        snapshot: The snapshot data
        output_dir: Directory to write the snapshot

    Returns:
        Path to the written file
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime('%Y%m%d_%H%M%S')
    commit_short = snapshot.get('commit', {}).get('short', 'unknown')

    filename = f'stats_{timestamp}_{commit_short}.json'
    filepath = output_path / filename

    with filepath.open('w') as f:
        json.dump(snapshot, f, indent=2)

    return filepath


def generate_snapshot(events_path: str | None = None, output_dir: str | None = None) -> Path | None:
    """Generate a snapshot from the latest events.

    Args:
        events_path: Path to events.jsonl (uses config default if None)
        output_dir: Directory to write snapshot (uses stats/ if None)

    Returns:
        Path to the generated snapshot, or None if no commit events found
    """
    config = load_config()

    if events_path is None:
        events_path = config.get('events_path', 'stats/events/events.jsonl')
    if output_dir is None:
        output_dir = 'stats'

    events = read_events_backwards(events_path)
    if not events:
        print('No events found in events.jsonl')
        return None

    commit_event, collector_events, hook_events = find_latest_commit_events(events)

    if not commit_event:
        print('No commit events found')
        return None

    snapshot = build_snapshot(commit_event, collector_events, hook_events)
    filepath = write_snapshot(snapshot, output_dir)

    print(f'Snapshot written to: {filepath}')
    return filepath


def main() -> int:
    """CLI entry point for snapshot generation."""
    filepath = generate_snapshot()
    return 0 if filepath else 1


if __name__ == '__main__':
    sys.exit(main())
