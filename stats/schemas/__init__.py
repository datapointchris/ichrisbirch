"""Event schemas with discriminated union for parsing.

This module exports:
- Event: A union type of all event types, discriminated by the 'type' field
- EventAdapter: A TypeAdapter for parsing Event from JSON
- parse_event: Parse a single JSON line into an Event
- parse_events_file: Parse a JSONL file into a list of Events
"""

from __future__ import annotations

from pathlib import Path

from pydantic import TypeAdapter

from stats.schemas.base import BaseEvent
from stats.schemas.collectors.coverage import CoverageCollectEvent
from stats.schemas.collectors.dependencies import DependenciesCollectEvent
from stats.schemas.collectors.docker import DockerCollectEvent
from stats.schemas.collectors.files import FilesCollectEvent
from stats.schemas.collectors.pytest_collector import PytestCollectEvent
from stats.schemas.collectors.radon import RadonCollectEvent
from stats.schemas.collectors.tokei import TokeiCollectEvent
from stats.schemas.commit import CommitEvent
from stats.schemas.hooks.actionlint import ActionlintHookEvent
from stats.schemas.hooks.bandit import BanditHookEvent
from stats.schemas.hooks.codespell import CodespellHookEvent
from stats.schemas.hooks.djlint import DjlintHookEvent
from stats.schemas.hooks.file_format import CheckJsonHookEvent
from stats.schemas.hooks.file_format import CheckTomlHookEvent
from stats.schemas.hooks.file_format import CheckYamlHookEvent
from stats.schemas.hooks.fixers import EndOfFileFixerHookEvent
from stats.schemas.hooks.fixers import TrailingWhitespaceHookEvent
from stats.schemas.hooks.markdownlint import MarkdownlintHookEvent
from stats.schemas.hooks.mypy import MypyHookEvent
from stats.schemas.hooks.pyupgrade import PyupgradeHookEvent
from stats.schemas.hooks.refurb import RefurbHookEvent
from stats.schemas.hooks.ruff import RuffHookEvent
from stats.schemas.hooks.shellcheck import ShellcheckHookEvent
from stats.schemas.hooks.uv_lock import UvLockHookEvent
from stats.schemas.hooks.validate_markdown_links import ValidateMarkdownLinksHookEvent

Event = (
    RuffHookEvent
    | MypyHookEvent
    | BanditHookEvent
    | ShellcheckHookEvent
    | CodespellHookEvent
    | RefurbHookEvent
    | PyupgradeHookEvent
    | MarkdownlintHookEvent
    | DjlintHookEvent
    | ActionlintHookEvent
    | CheckYamlHookEvent
    | CheckTomlHookEvent
    | CheckJsonHookEvent
    | TrailingWhitespaceHookEvent
    | EndOfFileFixerHookEvent
    | UvLockHookEvent
    | ValidateMarkdownLinksHookEvent
    | CommitEvent
    | TokeiCollectEvent
    | PytestCollectEvent
    | CoverageCollectEvent
    | DockerCollectEvent
    | DependenciesCollectEvent
    | FilesCollectEvent
    | RadonCollectEvent
)

EventAdapter: TypeAdapter[Event] = TypeAdapter(Event)


def parse_event(json_line: str) -> Event:
    """Parse a single JSON line into an Event.

    Uses Pydantic's discriminated union to determine the correct type
    based on the 'type' field in the JSON.

    Args:
        json_line: A single line of JSON representing an event

    Returns:
        The parsed event as the appropriate type
    """
    return EventAdapter.validate_json(json_line)


def parse_events_file(file_path: str) -> list[Event]:
    """Parse a JSONL file into a list of Events.

    Args:
        file_path: Path to the JSONL file

    Returns:
        List of parsed events, empty list if file doesn't exist
    """
    path = Path(file_path)

    if not path.exists():
        return []

    events: list[Event] = []
    content = path.read_text()

    for line in content.strip().split('\n'):
        if line:
            events.append(parse_event(line))

    return events


__all__ = [
    'BaseEvent',
    'Event',
    'EventAdapter',
    'parse_event',
    'parse_events_file',
    # Hooks
    'RuffHookEvent',
    'MypyHookEvent',
    'BanditHookEvent',
    'ShellcheckHookEvent',
    'CodespellHookEvent',
    'RefurbHookEvent',
    'PyupgradeHookEvent',
    'MarkdownlintHookEvent',
    'DjlintHookEvent',
    'ActionlintHookEvent',
    'CheckYamlHookEvent',
    'CheckTomlHookEvent',
    'CheckJsonHookEvent',
    'TrailingWhitespaceHookEvent',
    'EndOfFileFixerHookEvent',
    'UvLockHookEvent',
    'ValidateMarkdownLinksHookEvent',
    # Commit
    'CommitEvent',
    # Collectors
    'TokeiCollectEvent',
    'PytestCollectEvent',
    'CoverageCollectEvent',
    'DockerCollectEvent',
    'DependenciesCollectEvent',
    'FilesCollectEvent',
    'RadonCollectEvent',
]
