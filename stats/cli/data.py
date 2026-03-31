"""Data loading layer for stats CLI visualizations.

Replaces all jq pipelines in cli/stats with Python equivalents.
Functions read events.jsonl line-by-line with early filtering,
and load snapshot JSON files for the dashboard views.
"""

from __future__ import annotations

import json
from datetime import UTC
from datetime import datetime
from pathlib import Path


def load_events(
    events_path: str | Path,
    *,
    event_type: str | None = None,
    since: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    """Load events from a JSONL file with optional filtering.

    Reads line-by-line and applies filters before full JSON parsing
    to keep memory usage low on large files.  Events are returned in
    file order (oldest first).

    Args:
        events_path: Path to events.jsonl.
        event_type: If set, only include events whose ``type`` field
            matches exactly (e.g. ``"collect.pytest"``).
        since: ISO-8601 date or datetime string.  Events before this
            timestamp are skipped.  Compared lexicographically against
            the raw ``timestamp`` field for speed.
        limit: Maximum number of matching events to return.

    Returns:
        List of event dicts, oldest first.
    """
    path = Path(events_path)
    if not path.exists():
        return []

    # Pre-build a substring for fast grep-style line filtering.
    # This avoids json.loads on lines that can't possibly match.
    type_needle = f'"type":"{event_type}"' if event_type else None

    results: list[dict] = []
    with path.open() as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            # Fast substring pre-filter (same idea as grep piped to jq)
            if type_needle and type_needle not in line:
                continue

            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if event_type and event.get('type') != event_type:
                continue

            if since and event.get('timestamp', '') < since:
                continue

            results.append(event)
            if limit and len(results) >= limit:
                break

    return results


def load_events_reversed(
    events_path: str | Path,
    *,
    event_type: str | None = None,
    limit: int = 5000,
) -> list[dict]:
    """Load events from the end of a JSONL file, most recent first.

    Useful for queries that only need the latest N events without
    scanning the entire file.  Uses the same reverse-read strategy
    as ``stats.snapshot.read_events_backwards``.

    Args:
        events_path: Path to events.jsonl.
        event_type: If set, only include events whose ``type`` matches.
        limit: Maximum number of events to return.

    Returns:
        List of event dicts, most recent first.
    """
    path = Path(events_path)
    if not path.exists():
        return []

    type_needle = f'"type":"{event_type}"' if event_type else None

    # Read file backwards in chunks
    results: list[dict] = []
    chunk_size = 64 * 1024
    file_size = path.stat().st_size
    if file_size == 0:
        return []

    with path.open('rb') as f:
        remainder = b''
        position = file_size

        while position > 0 and len(results) < limit:
            read_size = min(chunk_size, position)
            position -= read_size
            f.seek(position)
            chunk = f.read(read_size) + remainder

            lines = chunk.split(b'\n')
            # First element may be a partial line — save for next chunk
            remainder = lines[0]

            # Process complete lines in reverse order
            for raw_line in reversed(lines[1:]):
                decoded = raw_line.decode('utf-8', errors='replace').strip()
                if not decoded:
                    continue

                if type_needle and type_needle not in decoded:
                    continue

                try:
                    event = json.loads(decoded)
                except json.JSONDecodeError:
                    continue

                if event_type and event.get('type') != event_type:
                    continue

                results.append(event)
                if len(results) >= limit:
                    break

        # Handle the very first line of the file
        if len(results) < limit and remainder:
            decoded = remainder.decode('utf-8', errors='replace').strip()
            if decoded and (not type_needle or type_needle in decoded):
                try:
                    event = json.loads(decoded)
                    if not event_type or event.get('type') == event_type:
                        results.append(event)
                except json.JSONDecodeError:
                    pass

    return results


def load_snapshot(data_dir: str | Path) -> dict | None:
    """Load the most recent stats snapshot JSON file.

    Looks for ``stats_*.json`` files in ``data_dir`` and returns the
    one with the most recent modification time (same as the bash
    ``stats-latest-file`` function).

    Args:
        data_dir: Directory containing snapshot files
            (typically ``stats/data/``).

    Returns:
        Parsed snapshot dict, or ``None`` if no snapshots exist.
    """
    data_path = Path(data_dir)
    if not data_path.is_dir():
        return None

    snapshots = sorted(data_path.glob('stats_*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not snapshots:
        return None

    with snapshots[0].open() as f:
        return json.loads(f.read())


def events_by_date(events: list[dict]) -> dict[str, list[dict]]:
    """Group events by their date (YYYY-MM-DD from timestamp field).

    This is the Python equivalent of the jq pattern:
    ``group_by(.timestamp[0:10])``

    Args:
        events: List of event dicts with ``timestamp`` fields.

    Returns:
        Dict mapping date strings to lists of events for that date.
    """
    grouped: dict[str, list[dict]] = {}
    for event in events:
        ts = event.get('timestamp', '')
        date_key = ts[:10]
        if date_key:
            grouped.setdefault(date_key, []).append(event)
    return grouped


def date_range(days: int) -> str:
    """Return an ISO date string N days ago, for use as a ``since`` filter."""
    from datetime import timedelta

    dt = datetime.now(UTC) - timedelta(days=days)
    return dt.strftime('%Y-%m-%d')


# ── Hook quality aggregation ────────────────────────────────────────

# Maps tool name → the JSON field that holds its issues list.
# Mirrors the bash get_issue_field() case statement.
ISSUE_FIELD_MAP: dict[str, str] = {
    'mypy': 'errors',
    'vue-typecheck': 'errors',
    'ruff-format': 'files_reformatted',
    'vue-prettier': 'files_reformatted',
    'terraform-fmt': 'files_reformatted',
    'pyupgrade': 'rewritten_files',
    'shellcheck': 'comments',
    'vue-eslint': 'messages',
    'end-of-file-fixer': 'fixed_files',
    'trailing-whitespace': 'fixed_files',
    'validate-markdown-links': 'broken_links',
    'check-executables-have-shebangs': 'files_without_shebangs',
    'check-shebang-scripts-are-executable': 'files_not_executable',
}

# The ordered list of tools shown in the quality matrix.
QUALITY_TOOLS = [
    # Python
    'ruff-check',
    'ruff-format',
    'mypy',
    'bandit',
    'codespell',
    'refurb',
    'pyupgrade',
    # Shell / Docker / Terraform
    'shellcheck',
    'hadolint',
    'docker-compose-validate',
    'terraform-validate',
    'terraform-tflint',
    'terraform-fmt',
    'terraform-docs',
    # File format / fixers
    'check-yaml',
    'check-toml',
    'check-json',
    'check-executables-have-shebangs',
    'check-shebang-scripts-are-executable',
    'detect-private-key',
    'end-of-file-fixer',
    'trailing-whitespace',
    # Frontend
    'sass',
    'vue-eslint',
    'vue-prettier',
    'vue-typecheck',
    # Docs / validation
    'markdownlint',
    'djlint',
    'actionlint',
    'validate-html',
    'validate-markdown-links',
    # Project
    'code-sync',
    'generate-fixture-diagrams',
    'uv-lock',
]


def _issue_count(event: dict, tool: str) -> int:
    """Count issues in a single hook event based on its tool-specific field."""
    field = ISSUE_FIELD_MAP.get(tool, 'issues')
    value = event.get(field, [])
    return len(value) if isinstance(value, list) else 0


def aggregate_hook_issues(events_path: str | Path) -> dict[str, dict[str, int]]:
    """Aggregate issue counts per tool per date from all hook events.

    Scans the events file once and builds a nested dict:
    ``{tool_name: {date_str: total_issues}}``.

    This replaces the bash loop that grep'd the file 124 times
    (31 tools × 4 time windows).
    """
    all_hooks = load_events(events_path, event_type=None)

    result: dict[str, dict[str, int]] = {}
    for event in all_hooks:
        event_type = event.get('type', '')
        if not event_type.startswith('hook.'):
            continue

        tool = event_type.removeprefix('hook.')
        date_key = event.get('timestamp', '')[:10]
        if not date_key:
            continue

        count = _issue_count(event, tool)
        tool_dates = result.setdefault(tool, {})
        tool_dates[date_key] = tool_dates.get(date_key, 0) + count

    return result


def sum_issues_in_window(tool_dates: dict[str, int], days: int | None = None) -> int:
    """Sum issue counts within a time window.

    Args:
        tool_dates: {date_str: count} for a single tool.
        days: Number of days back from today. None means all time.
    """
    if days is None:
        return sum(tool_dates.values())

    cutoff = date_range(days)
    return sum(count for date_str, count in tool_dates.items() if date_str >= cutoff)


def hook_run_summary(events_path: str | Path) -> list[dict]:
    """Compute hook run counts and failure rates across time periods.

    Returns a list of dicts with keys: label, days, runs, failed, pct.
    """
    all_hooks = load_events(events_path, event_type=None)

    # Collect all hook events with date + status
    hook_events: list[tuple[str, bool]] = []
    for event in all_hooks:
        if not event.get('type', '').startswith('hook.'):
            continue
        date_key = event.get('timestamp', '')[:10]
        is_failed = event.get('status') == 'failed'
        if date_key:
            hook_events.append((date_key, is_failed))

    periods = [
        ('Today', 1),
        ('Last 7d', 7),
        ('Last 14d', 14),
        ('Last 30d', 30),
        ('Last 60d', 60),
        ('Last 90d', 90),
    ]

    results = []
    for label, days in periods:
        cutoff = date_range(days)
        runs = sum(1 for d, _ in hook_events if d >= cutoff)
        failed = sum(1 for d, f in hook_events if d >= cutoff and f)
        pct = round(failed * 100 / runs, 1) if runs > 0 else 0.0
        results.append({'label': label, 'days': days, 'runs': runs, 'failed': failed, 'pct': pct})

    return results


# ── Test data aggregation ──────────────────────────────────────────


def _aggregate_test_type_by_day(events: list[dict]) -> dict[str, dict]:
    """Aggregate test events by date, computing per-day averages.

    Replaces the jq pattern:
        group_by(.timestamp[0:10]) | map({date, avg_tests, avg_duration, ...})

    Returns:
        Dict mapping date strings to aggregated stats dicts with keys:
        tests, duration, failed, passed.
    """
    by_date = events_by_date(events)
    result: dict[str, dict] = {}

    for date_key, day_events in by_date.items():
        n = len(day_events)
        tests_list = []
        dur_list = []
        failed_list = []
        passed_list = []

        for e in day_events:
            summary = e.get('summary', {})
            total = summary.get('total', 0)
            skipped = summary.get('skipped') or 0
            tests_list.append(total - skipped)
            dur_list.append(e.get('duration_seconds', 0))
            failed_list.append(summary.get('failed', 0))
            passed_list.append(summary.get('passed', 0))

        result[date_key] = {
            'tests': int(sum(tests_list) / n),
            'duration': int(sum(dur_list) / n),
            'failed': sum(failed_list),
            'passed': int(sum(passed_list) / n),
        }

    return result


def merge_test_trends(events_path: str | Path, days: int = 7) -> list[dict]:
    """Merge pytest + vitest daily trends into combined rows.

    Replaces the jq timestamp-proximity LEFT JOIN that merges
    pytest and vitest daily aggregates by date.

    Returns:
        List of dicts with keys: date, tests, duration, failed, passed,
        pass_pct — sorted by date descending, limited to ``days`` entries.
    """
    pytest_events = load_events(events_path, event_type='collect.pytest')
    vitest_events = load_events(events_path, event_type='collect.vitest')

    pytest_by_day = _aggregate_test_type_by_day(pytest_events)
    vitest_by_day = _aggregate_test_type_by_day(vitest_events)

    # Merge: use pytest dates as the base, add vitest where date matches
    merged = []
    for date_key in sorted(pytest_by_day.keys()):
        py = pytest_by_day[date_key]
        vi = vitest_by_day.get(date_key, {'tests': 0, 'duration': 0, 'failed': 0, 'passed': 0})

        tests = py['tests'] + vi['tests']
        passed = py['passed'] + vi['passed']
        pass_pct = int((passed * 100) / tests) if tests > 0 else 0

        merged.append(
            {
                'date': date_key,
                'tests': tests,
                'duration': py['duration'] + vi['duration'],
                'failed': py['failed'] + vi['failed'],
                'passed': passed,
                'pass_pct': pass_pct,
            }
        )

    # Last N days, most recent first
    return list(reversed(merged[-days:]))


def merge_test_history(events_path: str | Path, limit: int = 25) -> list[dict]:
    """Merge pytest + vitest events by timestamp proximity for the history chart.

    For each pytest run, finds a vitest event on the same date and adds
    the counts together.  This replaces the jq timestamp-proximity join
    that matched events within the same day.

    Returns:
        List of dicts with keys: duration, tests — oldest first,
        limited to the last ``limit`` entries.
    """
    pytest_events = load_events(events_path, event_type='collect.pytest')
    vitest_events = load_events(events_path, event_type='collect.vitest')

    # Build date→first vitest event lookup
    vitest_by_date: dict[str, dict] = {}
    for e in vitest_events:
        date_key = e.get('timestamp', '')[:10]
        if date_key and date_key not in vitest_by_date:
            vitest_by_date[date_key] = e

    # Filter out bad data (runs with 0 tests) and merge
    history = []
    for pe in pytest_events:
        summary = pe.get('summary', {})
        if summary.get('total', 0) == 0:
            continue

        py_tests = summary.get('total', 0) - (summary.get('skipped') or 0)
        py_dur = int(pe.get('duration_seconds', 0))

        date_key = pe.get('timestamp', '')[:10]
        ve = vitest_by_date.get(date_key)
        if ve:
            vs = ve.get('summary', {})
            vi_tests = vs.get('total', 0) - (vs.get('skipped') or 0)
            vi_dur = int(ve.get('duration_seconds', 0))
        else:
            vi_tests = 0
            vi_dur = 0

        history.append(
            {
                'duration': py_dur + vi_dur,
                'tests': py_tests + vi_tests,
            }
        )

    return history[-limit:]


def aggregate_slowest_tests(events_path: str | Path, top_n: int = 12) -> list[dict]:
    """Aggregate test durations by file path from the latest pytest run.

    Replaces the jq pipeline that splits nodeids, groups by path,
    sums durations, and filters by threshold.

    Returns:
        List of dicts with keys: path, total, count — sorted by
        total duration descending.
    """
    latest = load_events_reversed(events_path, event_type='collect.pytest', limit=1)
    if not latest:
        return []

    tests = latest[0].get('tests', [])
    by_file: dict[str, dict] = {}

    for t in tests:
        nodeid = t.get('nodeid', '')
        file_path = nodeid.split('::')[0] if '::' in nodeid else nodeid

        # Shorten path: keep full path for deep test dirs,
        # truncate to 3 segments otherwise
        parts = file_path.split('/')
        if len(parts) > 2 and parts[1] == 'ichrisbirch' and parts[2] in ('api', 'app', 'frontend'):
            short = file_path
        else:
            short = '/'.join(parts[:3])

        dur = sum((t.get(phase) or {}).get('duration', 0) for phase in ('setup', 'call', 'teardown'))

        if short in by_file:
            by_file[short]['total'] += dur
            by_file[short]['count'] += 1
        else:
            by_file[short] = {'path': short, 'total': dur, 'count': 1}

    sorted_files = sorted(by_file.values(), key=lambda x: -x['total'])

    # Filter out files below 0.8% of grand total (same threshold as bash)
    grand_total = sum(f['total'] for f in sorted_files)
    if grand_total > 0:
        sorted_files = [f for f in sorted_files if f['total'] > grand_total * 0.008]

    return sorted_files[:top_n]


def tests_per_directory(events_path: str | Path, top_n: int = 10) -> list[dict]:
    """Count tests per directory from the latest pytest run.

    Returns:
        List of dicts with keys: dir, count — sorted by count descending.
    """
    latest = load_events_reversed(events_path, event_type='collect.pytest', limit=1)
    if not latest:
        return []

    dir_counts: dict[str, int] = {}
    for t in latest[0].get('tests', []):
        nodeid = t.get('nodeid', '')
        # Strip ::ClassName::method to get just the file path
        file_path = nodeid.split('::')[0] if '::' in nodeid else nodeid
        parts = file_path.split('/')

        if len(parts) > 3 and parts[1] == 'ichrisbirch' and parts[2] in ('api', 'app'):
            dir_key = '/'.join(parts[:4])
        else:
            dir_key = '/'.join(parts[:3])

        dir_counts[dir_key] = dir_counts.get(dir_key, 0) + 1

    sorted_dirs = sorted(dir_counts.items(), key=lambda x: -x[1])
    return [{'dir': d, 'count': c} for d, c in sorted_dirs[:top_n]]


def detect_flaky_tests(events_path: str | Path, top_n: int = 5) -> list[dict]:
    """Find tests that have failed in some runs across all recorded events.

    Replaces the jq pipeline that groups all test outcomes by nodeid
    and counts failures.

    Returns:
        List of dicts with keys: test, failures — sorted by failure
        count descending.
    """
    all_pytest = load_events(events_path, event_type='collect.pytest')

    failure_counts: dict[str, int] = {}
    for event in all_pytest:
        for t in event.get('tests', []):
            if t.get('outcome') == 'failed':
                nodeid = t.get('nodeid', '')
                failure_counts[nodeid] = failure_counts.get(nodeid, 0) + 1

    sorted_flaky = sorted(failure_counts.items(), key=lambda x: -x[1])
    return [{'test': name, 'failures': count} for name, count in sorted_flaky[:top_n]]
