"""Refurb hook event schema - captures Python improvement suggestions."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class RefurbIssue(BaseModel):
    """A single refurb improvement suggestion."""

    path: str
    line: int
    column: int
    code: str  # e.g., "FURB110", "FURB146"
    message: str


class RefurbHookEvent(BaseEvent):
    """Event for refurb Python improvement suggestions hook."""

    type: Literal['hook.refurb'] = 'hook.refurb'
    status: Literal['passed', 'failed']
    exit_code: int
    issues: list[RefurbIssue]
    files_checked: list[str]
    duration_seconds: float
