"""Render project trend metrics with Rich tables and charts.

Replaces the bash ``stats-trends`` function: commit velocity,
code churn, test suite snapshot, Python LOC, daily commits
heatmap, and commit time-of-day histogram.

Usage from bash dispatch:
    python -m stats.cli.trends_view "$STATS_DATA_DIR"
"""

from __future__ import annotations

import subprocess  # nosec B404 — only used for git commands with list args
import sys
from datetime import UTC
from datetime import datetime
from datetime import timedelta

from rich.console import Console

from stats.cli.charts import vertical_bars
from stats.cli.data import load_snapshot


def _git(args: list[str]) -> str:
    """Run a git command and return stripped stdout."""
    result = subprocess.run(  # nosec B603 B607 — fixed git binary, no shell
        ['git', *args],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _count_lines(text: str) -> int:
    """Count non-empty lines."""
    if not text:
        return 0
    return len([line for line in text.splitlines() if line.strip()])


def _numstat_totals(since: str, path_filter: str | None = None) -> tuple[int, int]:
    """Get total added/deleted lines from git log --numstat.

    Returns (added, deleted) tuple.
    """
    args = ['log', f'--since={since}', '--numstat', '--pretty=']
    if path_filter:
        args.extend(['--', path_filter])
    output = _git(args)
    added = 0
    deleted = 0
    for line in output.splitlines():
        parts = line.split('\t')
        if len(parts) == 3 and parts[0] != '-':
            added += int(parts[0])
            deleted += int(parts[1])
    return added, deleted


def _delta_str(current: int, previous: int) -> str:
    """Format a percentage change with colored arrow."""
    if previous == 0:
        return ''
    change = (current - previous) * 100 // previous
    if change > 0:
        return f" ([green]\u2191{change}%[/green] vs prev week's {previous})"
    if change < 0:
        return f" ([red]\u2193{abs(change)}%[/red] vs prev week's {previous})"
    return ' (same as prev week)'


def _net_str(net: int) -> str:
    """Format a net line change with color."""
    if net >= 0:
        return f'[green]+{net:,}[/green]'
    return f'[red]{net:,}[/red]'


def _render_commit_velocity(con: Console) -> None:
    """Commit counts for today, 7d, 30d with delta vs previous period."""
    today = _count_lines(_git(['log', '--oneline', '--since=midnight']))
    week = _count_lines(_git(['log', '--oneline', '--since=7 days ago']))
    month = _count_lines(_git(['log', '--oneline', '--since=30 days ago']))
    prev_week = _count_lines(_git(['log', '--oneline', '--since=14 days ago', '--until=7 days ago']))

    con.print('[bold blue]Commit Velocity[/bold blue]')
    con.print(f'  {"Today:":<14} {today} commits')
    delta = _delta_str(week, prev_week) if prev_week > 0 else ''
    con.print(f'  {"Last 7 days:":<14} {week} commits{delta}')
    con.print(f'  {"Last 30 days:":<14} {month} commits')
    con.print()


def _render_code_churn(con: Console) -> None:
    """Lines added/deleted for 7d and 30d."""
    w_add, w_del = _numstat_totals('7 days ago')
    m_add, m_del = _numstat_totals('30 days ago')

    con.print('[bold blue]Code Churn (lines changed)[/bold blue]')
    con.print(f'  {"Last 7 days:":<14} [green]+{w_add:,}[/green] / [red]-{w_del:,}[/red]')
    con.print(f'  {"Last 30 days:":<14} [green]+{m_add:,}[/green] / [red]-{m_del:,}[/red]')
    con.print()


def _safe_int(value: int | float | str | None, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _safe_float(value: int | float | str | None, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _render_test_suite(con: Console, snap: dict | None) -> None:
    """Test suite summary from snapshot."""
    con.print('[bold blue]Test Suite (from latest snapshot)[/bold blue]')
    if not snap:
        con.print('  [dim]No stats snapshots found[/dim]')
        con.print()
        return

    tests = snap.get('tests', {})
    fe = snap.get('frontend_tests', {})
    e2e = snap.get('e2e_tests', {})

    py_t = _safe_int(tests.get('active', tests.get('total')))
    fe_t = _safe_int(fe.get('active', fe.get('total')))
    e2e_t = _safe_int(e2e.get('total'))
    all_t = py_t + fe_t + e2e_t

    all_failed = sum(_safe_int(s.get('failed')) for s in (tests, fe, e2e))
    all_skipped = sum(_safe_int(s.get('skipped')) for s in (tests, fe, e2e))
    all_dur = sum(_safe_float(s.get('duration_seconds')) for s in (tests, fe, e2e))
    cov = _safe_float(snap.get('coverage', {}).get('line_percent'))

    status = f'([red]{all_failed} failed[/red])' if all_failed > 0 else '([green]all passing[/green])'
    con.print(f'  {"Active:":<14} {all_t} tests {status}')
    con.print(f'    Python:    {py_t}')
    con.print(f'    Frontend:  {fe_t}')
    if e2e_t > 0:
        con.print(f'    E2E:       {e2e_t}')
    if all_skipped > 0:
        con.print(f'  {"Skipped:":<14} [yellow]{all_skipped}[/yellow]')
    if cov > 0:
        con.print(f'  {"Coverage:":<14} {cov:.1f}%')
    else:
        con.print(f'  {"Coverage:":<14} [dim]not collected[/dim]')
    con.print(f'  {"Duration:":<14} {all_dur:.0f}s')
    con.print()


def _render_python_loc(con: Console) -> None:
    """Python-specific line changes for 7d and 30d."""
    w_add, w_del = _numstat_totals('7 days ago', '*.py')
    m_add, m_del = _numstat_totals('30 days ago', '*.py')
    w_net = w_add - w_del
    m_net = m_add - m_del

    con.print('[bold blue]Python LOC (from git)[/bold blue]')
    con.print(f'  {"Last 7 days:":<14} {_net_str(w_net)} net ([green]+{w_add:,}[/green]/[red]-{w_del:,}[/red])')
    con.print(f'  {"Last 30 days:":<14} {_net_str(m_net)} net ([green]+{m_add:,}[/green]/[red]-{m_del:,}[/red])')
    con.print()


def _render_hot_files(con: Console) -> None:
    """Most frequently modified files in the last 7 days."""
    output = _git(['log', '--since=7 days ago', '--name-only', '--pretty=format:'])
    if not output:
        return

    counts: dict[str, int] = {}
    for line in output.splitlines():
        line = line.strip()
        if line:
            counts[line] = counts.get(line, 0) + 1

    sorted_files = sorted(counts.items(), key=lambda x: -x[1])[:5]
    con.print('[bold blue]Hot Files (7 days)[/bold blue]')
    for file, count in sorted_files:
        if count > 1:
            con.print(f'  {count:2d}x  {file}')
    con.print()


def _render_daily_commits(con: Console) -> None:
    """30-day daily commit chart using vertical bars."""
    today = datetime.now(UTC).astimezone().date()  # local date to match git --since/--until
    labels = []
    values = []

    for i in range(29, -1, -1):
        dt = today - timedelta(days=i)
        date_str = dt.strftime('%Y-%m-%d')
        dow = dt.strftime('%a')[0]
        count = _count_lines(_git(['log', '--oneline', f'--since={date_str} 00:00:00', f'--until={date_str} 23:59:59']))
        labels.append(dow)
        values.append(float(count))

    vertical_bars('Daily Commits (30 days)', labels, values, color='green', height=10, console=con)
    con.print()


def _render_hourly_histogram(con: Console) -> None:
    """Commit time-of-day distribution as vertical bars."""
    output = _git(['log', '--since=30 days ago', '--date=format:%H', '--format=%ad'])
    if not output:
        return

    buckets = [0] * 24
    for line in output.splitlines():
        line = line.strip()
        if line:
            hour = int(line)
            buckets[hour] += 1

    labels = [str(h) for h in range(24)]
    values = [float(b) for b in buckets]

    vertical_bars('Commit Time of Day (30 days)', labels, values, color='cyan', height=10, console=con)


def render(data_dir: str, *, console: Console | None = None) -> None:
    """Render the full trends view.

    Args:
        data_dir: Directory containing snapshot files.
        console: Rich Console (created if not provided).
    """
    con = console or Console()
    snap = load_snapshot(data_dir)

    con.print()
    con.print('[bold green]Project Trends[/bold green]')
    con.print()

    _render_commit_velocity(con)
    _render_code_churn(con)
    _render_test_suite(con, snap)
    _render_python_loc(con)
    _render_hot_files(con)
    _render_daily_commits(con)
    _render_hourly_histogram(con)


if __name__ == '__main__':
    stats_data_dir = sys.argv[1] if len(sys.argv) > 1 else 'stats/data'
    render(stats_data_dir)
