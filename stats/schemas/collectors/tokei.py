"""Tokei collector event schema - captures ALL tokei output."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class TokeiFileStats(BaseModel):
    """Stats for a single file."""

    blanks: int
    code: int
    comments: int


class TokeiFile(BaseModel):
    """A single file in the tokei report."""

    name: str
    stats: TokeiFileStats


class TokeiLanguageStats(BaseModel):
    """Stats for a single language."""

    blanks: int
    code: int
    comments: int
    files: list[TokeiFile]
    inaccurate: bool = False


class TokeiCollectEvent(BaseEvent):
    """Event for tokei code statistics collection."""

    type: Literal['collect.tokei'] = 'collect.tokei'
    languages: dict[str, TokeiLanguageStats]
    total_code: int
    total_comments: int
    total_blanks: int
    total_files: int
    duration_seconds: float
