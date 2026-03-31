"""Render recent devstats events as a Rich table.

Replaces the jq ``def info`` pipeline in the bash ``stats-events``
function with a typed extractor map and Rich Table output.

Usage from bash dispatch:
    python -m stats.cli.events_view "$STATS_EVENTS_FILE" [count]
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from math import floor

from rich.console import Console
from rich.table import Table

from stats.cli.data import load_events_reversed

# Event type → (value_extractor, label) mapping.
# Each extractor takes an event dict and returns a display string.
# This replaces the 10-branch jq ``def info`` conditional.
TYPE_EXTRACTORS: dict[str, tuple[Callable[[dict], str], str]] = {
    'commit': (lambda e: e.get('short_hash', '-'), ''),
    'collect.tokei': (lambda e: str(e.get('total_files', '-')), 'files'),
    'collect.pytest': (
        lambda e: str(e.get('summary', {}).get('total', 0) - (e.get('summary', {}).get('skipped') or 0)),
        'tests',
    ),
    'collect.coverage': (
        lambda e: f'{floor(e.get("summary", {}).get("percent_covered", 0))}%',
        'coverage',
    ),
    'collect.docker': (lambda e: str(len(e.get('images', []))), 'images'),
    'collect.dependencies': (lambda e: str(e.get('total_count', '-')), 'pkgs'),
    'collect.files': (lambda e: str(e.get('total_files', '-')), 'files'),
    'collect.radon': (
        lambda e: str(floor(e.get('avg_complexity', 0))),
        'avg_complexity',
    ),
    'collect.vitest': (
        lambda e: str(e.get('summary', {}).get('total', 0) - (e.get('summary', {}).get('skipped') or 0)),
        'fe_tests',
    ),
    'collect.playwright': (
        lambda e: str(e.get('summary', {}).get('total', 0) - (e.get('summary', {}).get('skipped') or 0)),
        'e2e_tests',
    ),
    'collect.npm_dependencies': (lambda e: str(e.get('total_count', '-')), 'npm_pkgs'),
}

# Color mapping for event type categories
TYPE_COLORS = {
    'commit': 'bold cyan',
    'collect': 'green',
    'hook': 'yellow',
}


def _extract_info(event: dict) -> tuple[str, str]:
    """Extract display value and label from an event."""
    event_type = event.get('type', '')

    extractor = TYPE_EXTRACTORS.get(event_type)
    if extractor:
        return extractor[0](event), extractor[1]

    # Hook events: show status
    if event.get('status'):
        return event['status'], ''

    return '-', ''


def _type_color(event_type: str) -> str:
    """Return a Rich style string for an event type."""
    if event_type in TYPE_COLORS:
        return TYPE_COLORS[event_type]
    prefix = event_type.split('.')[0]
    return TYPE_COLORS.get(prefix, 'white')


def render(events_path: str, count: int = 20, *, console: Console | None = None) -> None:
    """Render a table of recent events.

    Args:
        events_path: Path to events.jsonl.
        count: Number of recent events to show.
        console: Rich Console (created if not provided).
    """
    con = console or Console()
    events = load_events_reversed(events_path, limit=count)

    if not events:
        con.print('[yellow]No events found.[/yellow]')
        return

    # Reverse so oldest is at top, most recent at bottom (natural reading order)
    events.reverse()

    table = Table(
        show_header=True,
        header_style='bold',
        show_lines=False,
        pad_edge=False,
        box=None,
        padding=(0, 2),
    )
    table.add_column('Type', style='dim', min_width=28)
    table.add_column('Time', style='dim', width=8, justify='right')
    table.add_column('Value', justify='right', width=8)
    table.add_column('Label', style='dim')

    for event in events:
        event_type = event.get('type', '')
        timestamp = event.get('timestamp', '')
        time_str = timestamp[11:19] if len(timestamp) >= 19 else timestamp
        value, label = _extract_info(event)
        color = _type_color(event_type)

        table.add_row(
            f'[{color}]{event_type}[/{color}]',
            time_str,
            value,
            label,
        )

    con.print()
    con.print('[bold green]Recent Events[/bold green]')
    con.print()
    con.print(table)


if __name__ == '__main__':
    events_file = sys.argv[1] if len(sys.argv) > 1 else 'stats/data/events/events.jsonl'
    event_count = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    render(events_file, event_count)
