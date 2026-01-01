"""Codespell hook event schema - captures ALL codespell output."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class CodespellIssue(BaseModel):
    """A single codespell typo finding."""

    filename: str
    line: int
    word: str
    correction: str


class CodespellHookEvent(BaseEvent):
    """Event for codespell spelling check hook."""

    type: Literal['hook.codespell'] = 'hook.codespell'
    status: Literal['passed', 'failed']
    exit_code: int
    issues: list[CodespellIssue]
    files_checked: list[str]
    duration_seconds: float
