"""Files collector event schema - captures file statistics."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class FileTypeStats(BaseModel):
    """Statistics for a single file type."""

    extension: str
    count: int
    total_size_bytes: int


class FilesCollectEvent(BaseEvent):
    """Event for file statistics collection."""

    type: Literal['collect.files'] = 'collect.files'
    file_types: list[FileTypeStats]
    total_files: int
    total_size_bytes: int
    duration_seconds: float
