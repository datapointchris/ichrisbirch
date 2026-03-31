"""Render project dashboard and code statistics with Rich.

Replaces both ``stats-summary`` and ``stats-code`` bash functions.
The summary composes data from tokei, snapshot JSON, and events.jsonl
into a single dashboard view.

Usage from bash dispatch:
    python -m stats.cli.dashboard summary "$STATS_DATA_DIR" "$STATS_EVENTS_FILE"
    python -m stats.cli.dashboard code
"""

from __future__ import annotations

import json
import subprocess  # nosec B404 — only used for tokei with list args
import sys
from pathlib import Path

from rich.console import Console

from stats.cli.data import date_range
from stats.cli.data import load_events
from stats.cli.data import load_snapshot


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


def _tokei_languages() -> list[dict]:
    """Run tokei and return language stats sorted by content lines descending.

    Each dict has keys: language, content, blanks, files.
    Content is max(code, comments) matching the bash convention.
    """
    result = subprocess.run(  # nosec B603 B607 — fixed tokei binary, no shell
        ['tokei', '.', '--compact', '--output', 'json'],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return []

    data = json.loads(result.stdout)
    languages = []
    for lang, stats in data.items():
        if lang == 'Total' or stats.get('code') is None:
            continue
        content = max(stats.get('code', 0), stats.get('comments', 0))
        languages.append(
            {
                'language': lang,
                'content': content,
                'blanks': stats.get('blanks', 0),
                'files': len(stats.get('reports', [])),
            }
        )

    return sorted(languages, key=lambda x: -x['content'])


def _render_code_section(con: Console, languages: list[dict]) -> None:
    """Render the top-5 code summary section."""
    if not languages:
        return

    total_content = sum(lang['content'] for lang in languages)
    con.print('[bold blue]Code[/bold blue]')
    for lang in languages[:5]:
        name = lang['language'] + ':'
        con.print(f'  {name:<13} {lang["content"]:>6,} lines ({lang["files"]} files)')
    con.print(f'  [cyan]{"Total:":<13} {total_content:>6,} lines[/cyan]')
    con.print()


def _render_tests_section(con: Console, snap: dict) -> None:
    """Render the combined test results section from snapshot."""
    tests = snap.get('tests', {})
    fe = snap.get('frontend_tests', {})
    e2e = snap.get('e2e_tests', {})

    py_active = _safe_int(tests.get('active', tests.get('total')))
    fe_active = _safe_int(fe.get('active', fe.get('total')))
    e2e_active = _safe_int(e2e.get('total'))
    all_active = py_active + fe_active + e2e_active

    all_passed = sum(_safe_int(s.get('passed')) for s in (tests, fe, e2e))
    all_failed = sum(_safe_int(s.get('failed')) for s in (tests, fe, e2e))
    all_skipped = sum(_safe_int(s.get('skipped')) for s in (tests, fe, e2e))
    all_duration = sum(int(_safe_float(s.get('duration_seconds'))) for s in (tests, fe, e2e))
    coverage = _safe_float(snap.get('coverage', {}).get('line_percent'))

    pass_rate = (all_passed * 100 // all_active) if all_active > 0 else 0

    con.print('[bold blue]Tests[/bold blue]')
    if all_failed == 0:
        con.print(f'  {"Active:":<13} {all_active} tests ([green]{pass_rate}% pass[/green])')
    else:
        con.print(f'  {"Active:":<13} {all_active} tests ([red]{all_failed} failed[/red])')
    con.print(f'    Python:    {py_active}')
    con.print(f'    Frontend:  {fe_active}')
    if e2e_active > 0:
        con.print(f'    E2E:       {e2e_active}')
    if all_skipped > 0:
        con.print(f'  {"Skipped:":<13} [yellow]{all_skipped}[/yellow]')
    con.print(f'  {"Coverage:":<13} [cyan]{coverage:.1f}%[/cyan]')
    con.print(f'  {"Duration:":<13} {all_duration}s')
    con.print()


def _render_dependencies_section(con: Console, snap: dict) -> None:
    """Render the dependency counts section from snapshot."""
    deps_direct = _safe_int(snap.get('dependencies', {}).get('direct'))
    deps_total = _safe_int(snap.get('dependencies', {}).get('total'))
    npm_prod = _safe_int(snap.get('npm_dependencies', {}).get('production'))
    npm_dev = _safe_int(snap.get('npm_dependencies', {}).get('dev'))
    npm_total = _safe_int(snap.get('npm_dependencies', {}).get('total'))

    con.print('[bold blue]Dependencies[/bold blue]')
    con.print(f'  {"Python:":<13} {deps_direct} direct / {deps_total} total')
    if npm_total > 0:
        con.print(f'  {"npm:":<13} {npm_prod} prod / {npm_dev} dev / {npm_total} total')
    con.print()


def _render_activity_section(con: Console, events_path: str) -> None:
    """Render commit activity counts from events.jsonl."""
    if not Path(events_path).exists():
        return

    commit_events = load_events(events_path, event_type='commit')
    if not commit_events:
        return

    today_str = date_range(0)
    week_cutoff = date_range(7)

    total_commits = len(commit_events)
    today_commits = sum(1 for e in commit_events if e.get('timestamp', '')[:10] >= today_str)
    week_commits = sum(1 for e in commit_events if e.get('timestamp', '')[:10] >= week_cutoff)

    con.print('[bold blue]Activity[/bold blue]')
    con.print(f'  {"Today:":<13} {today_commits} commits')
    con.print(f'  {"This week:":<13} {week_commits} commits')
    con.print(f'  {"All time:":<13} {total_commits} commits')


def render_summary(data_dir: str, events_path: str, *, console: Console | None = None) -> None:
    """Render the project stats summary dashboard.

    Args:
        data_dir: Directory containing snapshot files.
        events_path: Path to events.jsonl.
        console: Rich Console (created if not provided).
    """
    con = console or Console()
    snap = load_snapshot(data_dir)

    con.print()
    con.print('[bold green]Project Stats Summary[/bold green]')
    con.print()

    if not snap:
        con.print('[yellow]No stats snapshots found.[/yellow]')
        con.print('Stats are collected automatically on each commit.')
        return

    collected_at = snap.get('collected_at', '')[:10]
    con.print(f'Last collected: [cyan]{collected_at}[/cyan]')
    con.print()

    _render_code_section(con, _tokei_languages())
    _render_tests_section(con, snap)
    _render_dependencies_section(con, snap)
    _render_activity_section(con, events_path)


def render_code(*, console: Console | None = None) -> None:
    """Render detailed code statistics by language.

    Args:
        console: Rich Console (created if not provided).
    """
    con = console or Console()

    con.print()
    con.print('[bold green]Code Statistics by Language[/bold green]')
    con.print()

    languages = _tokei_languages()
    if not languages:
        con.print('[yellow]tokei not found or no code to analyze[/yellow]')
        return

    con.print(f'[cyan]{"Language":<15} {"Content":>10} {"Blanks":>10} {"Files":>8}[/cyan]')
    con.print('\u2500' * 51)

    for lang in languages:
        con.print(f'{lang["language"]:<15} {lang["content"]:>10,} {lang["blanks"]:>10,} {lang["files"]:>8}')

    total_content = sum(lang['content'] for lang in languages)
    total_blanks = sum(lang['blanks'] for lang in languages)
    con.print('\u2500' * 51)
    con.print(f'[green]{"Total":<15} {total_content:>10,} {total_blanks:>10,}[/green]')


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'summary'
    if mode == 'code':
        render_code()
    else:
        stats_data_dir = sys.argv[2] if len(sys.argv) > 2 else 'stats/data'
        events_file = sys.argv[3] if len(sys.argv) > 3 else 'stats/data/events/events.jsonl'
        render_summary(stats_data_dir, events_file)
