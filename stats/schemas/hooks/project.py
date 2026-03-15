"""Project-specific hook schemas — code-sync, generate-fixture-diagrams, validate-html."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class CodeSyncHookEvent(BaseEvent):
    """Event for code-sync hook."""

    type: Literal['hook.code-sync'] = 'hook.code-sync'
    status: Literal['passed', 'failed']
    exit_code: int
    files_checked: list[str]
    duration_seconds: float


class GenerateFixtureDiagramsHookEvent(BaseEvent):
    """Event for generate-fixture-diagrams hook."""

    type: Literal['hook.generate-fixture-diagrams'] = 'hook.generate-fixture-diagrams'
    status: Literal['passed', 'failed']
    exit_code: int
    files_checked: list[str]
    duration_seconds: float


class HtmlValidationIssue(BaseModel):
    """A single HTML validation issue."""

    file: str
    line: int | None = None
    message: str
    level: str


class ValidateHtmlHookEvent(BaseEvent):
    """Event for validate-html hook — captures W3C validation issues."""

    type: Literal['hook.validate-html'] = 'hook.validate-html'
    status: Literal['passed', 'failed']
    exit_code: int
    issues: list[HtmlValidationIssue]
    files_checked: list[str]
    duration_seconds: float
