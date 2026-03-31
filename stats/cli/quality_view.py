"""Render code quality metrics as Rich tables.

Replaces the bash ``stats-quality`` function which grep'd the events
file 124+ times (31 tools × 4 time windows) to build the issue matrix.

Usage from bash dispatch:
    python -m stats.cli.quality_view "$STATS_EVENTS_FILE"
"""

from __future__ import annotations

import sys

from rich.console import Console
from rich.table import Table

from stats.cli.data import QUALITY_TOOLS
from stats.cli.data import aggregate_hook_issues
from stats.cli.data import hook_run_summary
from stats.cli.data import sum_issues_in_window


def _issue_cell(count: int) -> str:
    """Format an issue count with conditional coloring."""
    if count == 0:
        return '[dim]0[/dim]'
    return f'[yellow]{count}[/yellow]'


def _render_issue_matrix(con: Console, events_path: str) -> None:
    """Render the tool × time window issue matrix."""
    issues = aggregate_hook_issues(events_path)

    table = Table(
        show_header=True,
        header_style='bold cyan',
        box=None,
        pad_edge=False,
        padding=(0, 1),
    )
    table.add_column('Tool', min_width=38)
    table.add_column('24h', justify='right', width=6)
    table.add_column('7d', justify='right', width=6)
    table.add_column('30d', justify='right', width=6)
    table.add_column('All', justify='right', width=6)

    for tool in QUALITY_TOOLS:
        tool_dates = issues.get(tool, {})
        day1 = sum_issues_in_window(tool_dates, 1)
        day7 = sum_issues_in_window(tool_dates, 7)
        day30 = sum_issues_in_window(tool_dates, 30)
        total = sum_issues_in_window(tool_dates)

        table.add_row(
            tool,
            _issue_cell(day1),
            _issue_cell(day7),
            _issue_cell(day30),
            str(total) if total > 0 else '[dim]0[/dim]',
        )

    con.print(table)


def _render_hook_runs(con: Console, events_path: str) -> None:
    """Render hook run counts and failure rates with delta arrows."""
    runs = hook_run_summary(events_path)
    if not runs:
        return

    con.print()
    con.print('[bold blue]Hook Runs[/bold blue]')

    table = Table(
        show_header=True,
        header_style='bold cyan',
        box=None,
        pad_edge=False,
        padding=(0, 1),
    )
    table.add_column('Period', width=10)
    table.add_column('Runs', justify='right', width=7)
    table.add_column('Fail%', justify='right', width=7)
    table.add_column('vs Today', width=12)

    today_pct = runs[0]['pct'] if runs else 0.0

    for row in runs:
        pct_str = f'{row["pct"]}%'

        if row['days'] == 1:
            # Today row — no delta
            table.add_row(row['label'], str(row['runs']), pct_str, '')
        else:
            # Delta vs today
            if row['runs'] == 0 or (today_pct == 0 and row['pct'] == 0):
                delta_str = '[dim]--[/dim]'
            elif today_pct > 0:
                change = (row['pct'] - today_pct) * 100 / today_pct
                if change > 0:
                    delta_str = f'[red]\u2191{change:.1f}%[/red]'
                elif change < 0:
                    delta_str = f'[green]\u2193{abs(change):.1f}%[/green]'
                else:
                    delta_str = '[dim]--[/dim]'
            elif row['pct'] > 0:
                delta_str = f'[red]\u2191{row["pct"]:.1f}%[/red]'
            else:
                delta_str = '[dim]--[/dim]'

            table.add_row(row['label'], str(row['runs']), pct_str, delta_str)

    con.print(table)


def render(events_path: str, *, console: Console | None = None) -> None:
    """Render the full code quality view.

    Args:
        events_path: Path to events.jsonl.
        console: Rich Console (created if not provided).
    """
    con = console or Console()

    con.print()
    con.print('[bold green]Code Quality - Pre-commit Hook Results[/bold green]')
    con.print()

    _render_issue_matrix(con, events_path)
    _render_hook_runs(con, events_path)

    con.print()
    con.print('[dim]Note: Issues shown are from all pre-commit runs (including failed commits)[/dim]')


if __name__ == '__main__':
    events_file = sys.argv[1] if len(sys.argv) > 1 else 'stats/data/events/events.jsonl'
    render(events_file)
