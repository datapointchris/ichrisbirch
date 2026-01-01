"""Mypy hook event schema - captures all mypy errors with full details."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class MypyError(BaseModel):
    """Full mypy error - captures everything."""

    filename: str
    line: int
    column: int | None = None
    severity: Literal['error', 'warning', 'note']
    message: str
    code: str | None = None


class MypyHookEvent(BaseEvent):
    """Mypy hook event with full error details."""

    type: Literal['hook.mypy'] = 'hook.mypy'
    status: Literal['passed', 'failed']
    exit_code: int
    errors: list[MypyError]
    files_checked: list[str]
    duration_seconds: float
