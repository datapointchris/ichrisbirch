"""SASS compile hook event schema - captures SCSS compilation results."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class SassError(BaseModel):
    """A SASS compilation error."""

    message: str
    file: str | None = None
    line: int | None = None
    column: int | None = None


class SassHookEvent(BaseEvent):
    """Event for SASS compilation hook."""

    type: Literal['hook.sass'] = 'hook.sass'
    status: Literal['passed', 'failed']
    exit_code: int
    issues: list[SassError]
    files_checked: list[str]
    duration_seconds: float
