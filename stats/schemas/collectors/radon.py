"""Radon collector event schema - code complexity metrics."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class FunctionComplexity(BaseModel):
    """Complexity metrics for a single function."""

    name: str
    complexity: int
    rank: str
    lineno: int


class FileComplexity(BaseModel):
    """Complexity metrics for a single file."""

    path: str
    function_count: int
    total_complexity: int
    avg_complexity: float
    max_complexity: int
    maintainability_index: float
    maintainability_rank: str
    functions: list[FunctionComplexity]


class RadonCollectEvent(BaseEvent):
    """Radon complexity collection event."""

    type: Literal['collect.radon'] = 'collect.radon'
    files: list[FileComplexity]
    total_files: int
    avg_complexity: float
    avg_maintainability: float
    duration_seconds: float
