"""Fixer hook schemas - trailing-whitespace, end-of-file-fixer."""

from __future__ import annotations

from typing import Literal

from stats.schemas.base import BaseEvent


class TrailingWhitespaceHookEvent(BaseEvent):
    """Event for trailing-whitespace fixer hook."""

    type: Literal['hook.trailing-whitespace'] = 'hook.trailing-whitespace'
    status: Literal['passed', 'failed']
    exit_code: int
    fixed_files: list[str]
    files_checked: list[str]
    duration_seconds: float


class EndOfFileFixerHookEvent(BaseEvent):
    """Event for end-of-file-fixer hook."""

    type: Literal['hook.end-of-file-fixer'] = 'hook.end-of-file-fixer'
    status: Literal['passed', 'failed']
    exit_code: int
    fixed_files: list[str]
    files_checked: list[str]
    duration_seconds: float
