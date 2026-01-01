"""Ruff hook event schema - captures ALL ruff output with full issue details."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class RuffLocation(BaseModel):
    """Location in source code."""

    column: int
    row: int


class RuffEdit(BaseModel):
    """A single edit to fix an issue."""

    content: str
    location: RuffLocation
    end_location: RuffLocation


class RuffFix(BaseModel):
    """Fix information for an issue."""

    applicability: str
    edits: list[RuffEdit]
    message: str | None = None


class RuffIssue(BaseModel):
    """Full ruff issue - captures EVERYTHING ruff outputs."""

    code: str
    message: str
    filename: str
    location: RuffLocation
    end_location: RuffLocation
    fix: RuffFix | None = None
    noqa_row: int | None = None
    url: str | None = None
    cell: int | None = None


class RuffHookEvent(BaseEvent):
    """Ruff hook event with full issue details."""

    type: Literal['hook.ruff'] = 'hook.ruff'
    status: Literal['passed', 'failed']
    exit_code: int
    issues: list[RuffIssue]
    files_checked: list[str]
    duration_seconds: float
