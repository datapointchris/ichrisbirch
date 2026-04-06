"""Render commit activity as a Rich table with inline bars.

Replaces the bash ``stats-activity`` function which grep-counted
commits per day and rendered ``#`` character bars.

Usage from bash dispatch:
    python -m stats.cli.activity_view "$STATS_EVENTS_FILE" [days]
"""

from __future__ import annotations

import sys
from datetime import UTC
from datetime import datetime
from datetime import timedelta

from rich.console import Console
from rich.table import Table
from rich.text import Text

from stats.cli.charts import bar_str
from stats.cli.data import events_by_date
from stats.cli.data import load_events


def render(events_path: str, days: int = 7, *, console: Console | None = None) -> None:
    """Render commit activity for the last N days.

    Shows a table with date, day name, inline bar, and commit count,
    plus a total at the bottom.

    Args:
        events_path: Path to events.jsonl.
        days: Number of days to show (default 7).
        console: Rich Console (created if not provided).
    """
    con = console or Console()

    # Single scan of events file, filtered to commits
    # Local time: event timestamps use git author dates in local timezone
    local_now = datetime.now(UTC).astimezone()
    since_date = (local_now - timedelta(days=days)).strftime('%Y-%m-%d')
    commits = load_events(events_path, event_type='commit', since=since_date)
    by_date = events_by_date(commits)

    # Also count all commits for the total
    all_commits = load_events(events_path, event_type='commit')
    total = len(all_commits)

    # Build day list from most recent to oldest
    today = local_now.date()
    day_data: list[tuple[str, str, int]] = []
    for i in range(days):
        dt = today - timedelta(days=i)
        date_str = dt.strftime('%Y-%m-%d')
        day_name = dt.strftime('%a')
        count = len(by_date.get(date_str, []))
        day_data.append((date_str, day_name, count))

    max_count = max((d[2] for d in day_data), default=0)

    con.print()
    con.print(f'[bold green]Commit Activity (last {days} days)[/bold green]')
    con.print()

    table = Table(
        show_header=False,
        show_lines=False,
        pad_edge=False,
        box=None,
        padding=(0, 2),
    )
    table.add_column('Date', width=10)
    table.add_column('Day', width=3)
    table.add_column('Bar', min_width=25)
    table.add_column('Count', justify='right', width=4)

    for date_str, day_name, count in day_data:
        is_today = date_str == today.strftime('%Y-%m-%d')
        date_style = 'bold cyan' if is_today else ''
        bar = bar_str(count, max_count, 25, 'green') if count > 0 else Text('')

        row_count = Text(str(count))
        if count > 0:
            row_count.stylize('green')

        table.add_row(
            Text(date_str, style=date_style),
            Text(day_name, style=date_style),
            bar,
            row_count,
        )

    con.print(table)
    con.print()
    con.print(f'Total recorded commits: {total}')


if __name__ == '__main__':
    events_file = sys.argv[1] if len(sys.argv) > 1 else 'stats/data/events/events.jsonl'
    num_days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    render(events_file, num_days)
