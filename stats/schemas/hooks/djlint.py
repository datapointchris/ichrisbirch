"""Djlint hook event schema - captures Jinja/HTML template linting issues."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class DjlintIssue(BaseModel):
    """A single djlint linting issue."""

    path: str
    line: int
    column: int
    code: str  # e.g., "H005", "H006", "H013"
    message: str


class DjlintHookEvent(BaseEvent):
    """Event for djlint Jinja/HTML template linting hook."""

    type: Literal['hook.djlint'] = 'hook.djlint'
    status: Literal['passed', 'failed']
    exit_code: int
    issues: list[DjlintIssue]
    files_checked: list[str]
    duration_seconds: float
