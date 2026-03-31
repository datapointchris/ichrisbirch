"""Render test statistics with Rich tables and charts.

Replaces the 300-line bash ``stats-tests`` function which used
multiple jq pipelines for aggregation and hand-built ASCII charts.

Usage from bash dispatch:
    python -m stats.cli.tests_view "$STATS_EVENTS_FILE" "$STATS_DATA_DIR" [snapshot_file]
"""

from __future__ import annotations

import sys

from rich.console import Console
from rich.table import Table

from stats.cli.charts import horizontal_bars
from stats.cli.charts import vertical_bars
from stats.cli.data import aggregate_slowest_tests
from stats.cli.data import detect_flaky_tests
from stats.cli.data import load_snapshot
from stats.cli.data import merge_test_history
from stats.cli.data import merge_test_trends
from stats.cli.data import tests_per_directory


def _safe_int(value: int | float | str | None, default: int = 0) -> int:
    """Extract an int from a snapshot value that may be None or a string."""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _safe_float(value: int | float | str | None, default: float = 0.0) -> float:
    """Extract a float from a snapshot value that may be None or a string."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _render_current_results(con: Console, snap: dict) -> None:
    """Render the combined test results summary from snapshot data."""
    tests = snap.get('tests', {})
    fe = snap.get('frontend_tests', {})
    e2e = snap.get('e2e_tests', {})

    py_active = _safe_int(tests.get('active', tests.get('total')))
    py_passed = _safe_int(tests.get('passed'))
    py_failed = _safe_int(tests.get('failed'))
    py_skipped = _safe_int(tests.get('skipped'))
    py_errors = _safe_int(tests.get('errors'))
    py_dur = _safe_float(tests.get('duration_seconds'))
    coverage = _safe_float(snap.get('coverage', {}).get('line_percent'))

    fe_active = _safe_int(fe.get('active', fe.get('total')))
    fe_passed = _safe_int(fe.get('passed'))
    fe_failed = _safe_int(fe.get('failed'))
    fe_skipped = _safe_int(fe.get('skipped'))
    fe_dur = _safe_float(fe.get('duration_seconds'))

    e2e_active = _safe_int(e2e.get('total'))
    e2e_passed = _safe_int(e2e.get('passed'))
    e2e_failed = _safe_int(e2e.get('failed'))
    e2e_skipped = _safe_int(e2e.get('skipped'))
    e2e_dur = _safe_float(e2e.get('duration_seconds'))

    all_active = py_active + fe_active + e2e_active
    all_passed = py_passed + fe_passed + e2e_passed
    all_failed = py_failed + fe_failed + e2e_failed
    all_skipped = py_skipped + fe_skipped + e2e_skipped
    all_dur = py_dur + fe_dur + e2e_dur

    con.print('[bold blue]Current Results[/bold blue]')
    con.print(f'  Active:    {all_active}')
    con.print(f'    Python:    {py_active}')
    con.print(f'    Frontend:  {fe_active}')
    if e2e_active > 0:
        con.print(f'    E2E:       {e2e_active}')
    con.print(f'  Passed:    [green]{all_passed}[/green]')
    if all_failed > 0:
        con.print(f'  Failed:    [red]{all_failed}[/red]')
    if all_skipped > 0:
        con.print(f'  Skipped:   [yellow]{all_skipped}[/yellow]')
    if py_errors > 0:
        con.print(f'  Errors:    [red]{py_errors}[/red]')
    con.print(f'  Duration:  {all_dur:.0f}s')
    con.print(f'  Coverage:  {coverage:.1f}%')
    con.print()


def _render_trends(con: Console, events_path: str) -> None:
    """Render test suite trends table (by day)."""
    trends = merge_test_trends(events_path, days=7)
    if not trends:
        return

    con.print('[bold blue]Test Suite Trends (by day)[/bold blue]')

    table = Table(show_header=True, header_style='bold cyan', box=None, pad_edge=False, padding=(0, 2))
    table.add_column('Date', width=12)
    table.add_column('Tests', justify='right', width=6)
    table.add_column('Duration', justify='right', width=8)
    table.add_column('Failed', justify='right', width=6)
    table.add_column('Pass %', justify='right', width=8)

    for row in trends:
        failed_style = 'red' if row['failed'] > 0 else 'green'
        table.add_row(
            row['date'],
            str(row['tests']),
            f'{row["duration"]}s',
            f'[{failed_style}]{row["failed"]}[/{failed_style}]',
            f'{row["pass_pct"]}%',
        )

    con.print(table)
    con.print()


def _render_history_chart(con: Console, events_path: str) -> None:
    """Render the test suite history as a dual-series vertical bar chart."""
    history = merge_test_history(events_path, limit=25)
    if not history:
        return

    max_dur = max(h['duration'] for h in history) or 1
    max_tests = max(h['tests'] for h in history) or 1

    con.print('[bold blue]Test Suite History (last 25 runs)[/bold blue]')
    con.print(f'  [yellow]██[/yellow] Duration (max {max_dur}s)   [green]██[/green] Tests (max {max_tests})')

    durations = [float(h['duration']) for h in history]
    test_counts = [float(h['tests']) for h in history]
    # Use run indices as labels
    labels = [str(i + 1) for i in range(len(history))]

    vertical_bars(
        '',
        labels,
        durations,
        color='yellow',
        height=8,
        second_values=test_counts,
        second_color='green',
        console=con,
    )
    con.print()


def _render_slowest_files(con: Console, events_path: str) -> None:
    """Render slowest test files with horizontal bars."""
    slowest = aggregate_slowest_tests(events_path)
    if not slowest:
        return

    labels = []
    for f in slowest:
        short = f['path'].removeprefix('tests/ichrisbirch/').removeprefix('tests/')
        labels.append(short[:38])
    values = [f['total'] for f in slowest]

    horizontal_bars('Slowest Test Files', labels, values, color='yellow', value_suffix='s', console=con)
    con.print()


def _render_tests_per_dir(con: Console, events_path: str) -> None:
    """Render test count per directory."""
    dirs = tests_per_directory(events_path)
    if not dirs:
        return

    con.print('[bold blue]Tests per Directory[/bold blue]')
    table = Table(show_header=False, box=None, pad_edge=False, padding=(0, 2))
    table.add_column('Dir', min_width=40)
    table.add_column('Count', justify='right', width=10)

    for d in dirs:
        table.add_row(f'  {d["dir"]}', f'{d["count"]} tests')

    con.print(table)
    con.print()


def _render_flaky_tests(con: Console, events_path: str) -> None:
    """Render flaky test detection results."""
    con.print('[bold blue]Flaky Tests (failed in some runs)[/bold blue]')
    flaky = detect_flaky_tests(events_path)
    if flaky:
        for f in flaky:
            short_name = f['test'].split('::')[-1]
            con.print(f'  {f["failures"]}x  {short_name}')
    else:
        con.print('  [green]No flaky tests detected[/green]')
    con.print()


def _render_slowest_from_snapshot(con: Console, snap: dict, section: str, title: str, path_transform: str | None = None) -> None:
    """Render slowest tests from a snapshot section."""
    data = snap.get(section, {})
    slowest = data.get('slowest', [])
    if not slowest:
        return

    con.print(f'[bold blue]{title}[/bold blue]')
    for t in slowest[:8]:
        dur = str(t.get('duration', 0))[:5]
        name = t.get('name', '')
        if path_transform == 'python':
            name = name.replace('tests/ichrisbirch/', '').replace('::test_', ': ')
        elif path_transform == 'frontend':
            name = name.split('frontend/src/')[-1].replace('/__tests__', '').replace('.test.ts::', ': ')
        con.print(f'  {dur}s  {name}')
    con.print()


def _render_test_suite_details(con: Console, snap: dict, section: str, title: str, path_transform: str | None = None) -> None:
    """Render detailed test suite results from a snapshot section."""
    data = snap.get(section, {})
    active = _safe_int(data.get('active', data.get('total')))
    passed = _safe_int(data.get('passed'))
    failed = _safe_int(data.get('failed'))
    skipped = _safe_int(data.get('skipped'))
    duration = _safe_float(data.get('duration_seconds'))

    con.print(f'[bold blue]{title}[/bold blue]')

    if active == 0 and skipped == 0:
        con.print(f'  [dim]No {section.replace("_", " ")} results collected[/dim]')
        con.print()
        return

    con.print(f'  Active:    {active}')
    con.print(f'  Passed:    [green]{passed}[/green]')
    if failed > 0:
        con.print(f'  Failed:    [red]{failed}[/red]')
    if skipped > 0:
        con.print(f'  Skipped:   [yellow]{skipped}[/yellow]')
    con.print(f'  Duration:  {duration:.1f}s')
    con.print()

    _render_slowest_from_snapshot(con, snap, section, f'Slowest {title.split("(")[0].strip()}', path_transform)


def render(events_path: str, data_dir: str, snapshot_file: str | None = None, *, console: Console | None = None) -> None:
    """Render the full test statistics view.

    Args:
        events_path: Path to events.jsonl.
        data_dir: Directory containing snapshot files.
        snapshot_file: Explicit snapshot file path (uses latest if not given).
        console: Rich Console (created if not provided).
    """
    con = console or Console()

    snap = load_snapshot(data_dir) if not snapshot_file else None
    if snapshot_file:
        import json
        from pathlib import Path

        p = Path(snapshot_file)
        if p.exists():
            snap = json.loads(p.read_text())

    con.print()
    con.print('[bold green]Test Statistics[/bold green]')
    con.print()

    if not snap:
        con.print('[yellow]No stats snapshots found.[/yellow]')
        return

    _render_current_results(con, snap)
    _render_trends(con, events_path)
    _render_history_chart(con, events_path)
    _render_slowest_files(con, events_path)
    _render_tests_per_dir(con, events_path)
    _render_flaky_tests(con, events_path)
    _render_slowest_from_snapshot(con, snap, 'tests', 'Slowest Python Tests (latest run)', 'python')
    _render_test_suite_details(con, snap, 'frontend_tests', 'Frontend Test Details (Vitest)', 'frontend')
    _render_test_suite_details(con, snap, 'e2e_tests', 'E2E Test Details (Playwright)')


if __name__ == '__main__':
    events_file = sys.argv[1] if len(sys.argv) > 1 else 'stats/data/events/events.jsonl'
    stats_data_dir = sys.argv[2] if len(sys.argv) > 2 else 'stats/data'
    snap_file = sys.argv[3] if len(sys.argv) > 3 else None
    render(events_file, stats_data_dir, snap_file)
