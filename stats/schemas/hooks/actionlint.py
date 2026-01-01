"""Actionlint hook event schema - captures GitHub Actions workflow linting issues."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class ActionlintIssue(BaseModel):
    """A single actionlint issue."""

    message: str
    filepath: str
    line: int
    column: int
    kind: str  # e.g., "shellcheck", "workflow-call", "expression"
    snippet: str | None


class ActionlintHookEvent(BaseEvent):
    """Event for actionlint GitHub Actions workflow linting hook."""

    type: Literal['hook.actionlint'] = 'hook.actionlint'
    status: Literal['passed', 'failed']
    exit_code: int
    issues: list[ActionlintIssue]
    files_checked: list[str]
    duration_seconds: float
