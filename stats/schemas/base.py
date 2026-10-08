"""Base event schema shared by all event types."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel


class BaseEvent(BaseModel):
    """Fields shared by all events.

    All events capture:
    - timestamp: When the event occurred (UTC)
    - project: Project name (e.g., "ichrisbirch")
    - branch: Git branch name
    """

    timestamp: dt.datetime
    project: str
    branch: str
