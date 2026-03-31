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


def snapshot_path(data_dir: str | Path) -> Path | None:
    """Return the path to the most recent snapshot, or None."""
    data_path = Path(data_dir)
    if not data_path.is_dir():
        return None
    snapshots = sorted(data_path.glob('stats_*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
    return snapshots[0] if snapshots else None


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
