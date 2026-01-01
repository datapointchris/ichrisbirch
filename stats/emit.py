"""Event emission to JSONL file."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stats.schemas.base import BaseEvent


def emit_event(event: BaseEvent, events_path: str) -> None:
    """Append an event to the JSONL file.

    Creates parent directories if they don't exist.
    Each event is written as a single line of JSON, terminated by newline.

    Args:
        event: The event to emit (must be a Pydantic model)
        events_path: Path to the JSONL file
    """
    path = Path(events_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open('a') as f:
        f.write(event.model_dump_json())
        f.write('\n')
