"""Render code churn analysis with Rich tables.

Replaces both ``stats-churn`` and ``stats-churn-all`` bash functions.
All data comes from git log subprocess calls parsed in Python,
replacing the awk/grep/sort pipelines.

Usage from bash dispatch:
    python -m stats.cli.churn_view [days|all]
"""

from __future__ import annotations

import subprocess  # nosec B404 — only used for git commands with list args
import sys
from pathlib import Path

from rich.console import Console


def _git(args: list[str]) -> str:
    """Run a git command and return stripped stdout."""
    result = subprocess.run(  # nosec B603 B607 — fixed git binary, no shell
        ['git', *args],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _most_modified_files(since: str | None, limit: int) -> list[tuple[int, str]]:
    """Count how many commits touched each file."""
    args = ['log', '--name-only', '--pretty=format:']
    if since:
        args.insert(1, f'--since={since}')
    output = _git(args)

    counts: dict[str, int] = {}
    for line in output.splitlines():
        f = line.strip()
        if f and not f.endswith('.lock'):
            counts[f] = counts.get(f, 0) + 1

    return [(c, f) for f, c in sorted(counts.items(), key=lambda x: -x[1])[:limit]]


def _most_lines_changed(since: str | None, limit: int) -> list[tuple[int, int, int, str]]:
    """Aggregate added/deleted lines per file from git numstat."""
    args = ['log', '--numstat', '--pretty=format:']
    if since:
        args.insert(1, f'--since={since}')
    output = _git(args)

    adds: dict[str, int] = {}
    dels: dict[str, int] = {}
    for line in output.splitlines():
        parts = line.split('\t')
        if len(parts) == 3 and parts[0] != '-' and not parts[2].endswith('.lock'):
            f = parts[2]
            adds[f] = adds.get(f, 0) + int(parts[0])
            dels[f] = dels.get(f, 0) + int(parts[1])

    files = [(adds[f] + dels[f], adds[f], dels[f], f) for f in adds]
    return sorted(files, key=lambda x: -x[0])[:limit]


def _created_files(since: str, limit: int) -> list[str]:
    """Files added in the time window that still exist."""
    output = _git(['log', f'--since={since}', '--diff-filter=A', '--name-only', '--pretty=format:'])
    seen: set[str] = set()
    result: list[str] = []
    for line in output.splitlines():
        f = line.strip()
        if f and not f.endswith('.lock') and f not in seen:
            seen.add(f)
            if Path(f).exists():
                result.append(f)
    return result[-limit:]


def _deleted_files(since: str, limit: int) -> list[str]:
    """Files deleted in the time window."""
    output = _git(['log', f'--since={since}', '--diff-filter=D', '--name-only', '--pretty=format:'])
    seen: set[str] = set()
    result: list[str] = []
    for line in output.splitlines():
        f = line.strip()
        if f and not f.endswith('.lock') and f not in seen:
            seen.add(f)
            result.append(f)
    return result[-limit:]


def _churn_by_directory(since: str | None, limit: int) -> list[tuple[int, str]]:
    """Aggregate file changes by top-level directory pair."""
    args = ['log', '--name-only', '--pretty=format:']
    if since:
        args.insert(1, f'--since={since}')
    output = _git(args)

    counts: dict[str, int] = {}
    for line in output.splitlines():
        f = line.strip()
        if not f or '/' not in f:
            continue
        parts = f.split('/')
        if len(parts) >= 3:
            dir_key = f'{parts[0]}/{parts[1]}'
            counts[dir_key] = counts.get(dir_key, 0) + 1

    return [(c, d) for d, c in sorted(counts.items(), key=lambda x: -x[1])[:limit]]


def render(days: int | None = 30, *, console: Console | None = None) -> None:
    """Render code churn analysis.

    Args:
        days: Number of days to analyze. None means all time.
        console: Rich Console (created if not provided).
    """
    con = console or Console()
    since = f'{days} days ago' if days else None
    limit = 10 if days else 15

    con.print()
    if days:
        con.print(f'[bold green]Code Churn Analysis (last {days} days)[/bold green]')
    else:
        commit_count = _git(['rev-list', '--count', 'HEAD'])
        first_date = _git(['log', '--reverse', '--format=%cs']).splitlines()[0] if commit_count != '0' else '?'
        con.print(f'[bold green]Code Churn Analysis (all time - {commit_count} commits since {first_date})[/bold green]')
    con.print()

    # Most Modified Files
    modified = _most_modified_files(since, limit)
    if modified:
        con.print('[bold blue]Most Modified Files[/bold blue]')
        for count, f in modified:
            con.print(f'  {count:5d} changes  {f}')
        con.print()

    # Most Lines Changed
    lines_data = _most_lines_changed(since, limit)
    if lines_data:
        con.print('[bold blue]Most Lines Changed[/bold blue]')
        for line_total, line_added, line_deleted, line_file in lines_data:
            con.print(f'  {line_total:6d} lines  [green]+{line_added:<6d}[/green] [red]-{line_deleted:<6d}[/red]  {line_file}')
        con.print()

    # Created / Deleted (only for time-windowed mode)
    if days and since:
        created = _created_files(since, limit)
        if created:
            con.print('[bold blue]Recently Created Files[/bold blue]')
            for f in created:
                con.print(f'  [green]+[/green] {f}')
            con.print()

        deleted_files = _deleted_files(since, limit)
        if deleted_files:
            con.print('[bold blue]Recently Deleted Files[/bold blue]')
            for f in deleted_files:
                con.print(f'  [red]-[/red] {f}')
            con.print()

    # Churn by Directory
    dir_churn = _churn_by_directory(since, limit)
    if dir_churn:
        con.print('[bold blue]Churn by Directory[/bold blue]')
        for count, d in dir_churn:
            con.print(f'  {count:5d} changes  {d}/')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'all':
        render(days=None)
    elif len(sys.argv) > 1:
        render(days=int(sys.argv[1]))
    else:
        render(days=30)
