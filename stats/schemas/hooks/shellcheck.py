"""Shellcheck hook event schema - captures ALL shellcheck output."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class ShellcheckReplacement(BaseModel):
    """A single text replacement for a shellcheck fix."""

    column: int
    endColumn: int
    endLine: int
    insertionPoint: str
    line: int
    precedence: int
    replacement: str


class ShellcheckFix(BaseModel):
    """Fix information for a shellcheck comment."""

    replacements: list[ShellcheckReplacement]


class ShellcheckComment(BaseModel):
    """Full shellcheck comment with all fields."""

    file: str
    line: int
    endLine: int
    column: int
    endColumn: int
    level: Literal['error', 'warning', 'info', 'style']
    code: int
    message: str
    fix: ShellcheckFix | None = None


class ShellcheckHookEvent(BaseEvent):
    """Event for shellcheck linting hook."""

    type: Literal['hook.shellcheck'] = 'hook.shellcheck'
    status: Literal['passed', 'failed']
    exit_code: int
    comments: list[ShellcheckComment]
    files_checked: list[str]
    duration_seconds: float
