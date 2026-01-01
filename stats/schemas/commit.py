"""Commit event schema."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class StagedFile(BaseModel):
    """File that was staged for commit."""

    path: str
    status: Literal['added', 'modified', 'deleted', 'renamed']
    lines_added: int
    lines_removed: int


class CommitEvent(BaseEvent):
    """Commit event with full git info."""

    type: Literal['commit'] = 'commit'
    hash: str
    short_hash: str
    message: str
    author: str
    email: str
    files_changed: int
    insertions: int
    deletions: int
    staged_files: list[StagedFile]
