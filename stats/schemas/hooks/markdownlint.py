"""Markdownlint hook event schema - captures markdown linting issues."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class MarkdownlintIssue(BaseModel):
    """A single markdownlint issue."""

    file_name: str
    line_number: int
    rule_names: list[str]  # e.g., ["MD009", "no-trailing-spaces"]
    rule_description: str
    error_detail: str | None
    error_context: str | None
    severity: Literal['error', 'warning']


class MarkdownlintHookEvent(BaseEvent):
    """Event for markdownlint markdown quality check hook."""

    type: Literal['hook.markdownlint'] = 'hook.markdownlint'
    status: Literal['passed', 'failed']
    exit_code: int
    issues: list[MarkdownlintIssue]
    files_checked: list[str]
    duration_seconds: float
