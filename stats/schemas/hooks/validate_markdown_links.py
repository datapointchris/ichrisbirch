"""Validate-markdown-links hook schema."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class BrokenLink(BaseModel):
    """A broken markdown link."""

    path: str
    line: int
    link: str


class ValidateMarkdownLinksHookEvent(BaseEvent):
    """Event for validate-markdown-links hook."""

    type: Literal['hook.validate-markdown-links'] = 'hook.validate-markdown-links'
    status: Literal['passed', 'failed']
    exit_code: int
    broken_links: list[BrokenLink]
    files_checked: list[str]
    duration_seconds: float
