"""Coverage collector event schema - captures coverage report data."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class CoverageFileSummary(BaseModel):
    """Coverage summary for a single file."""

    filename: str
    covered_lines: int
    missing_lines: int
    excluded_lines: int
    percent_covered: float


class CoverageSummary(BaseModel):
    """Overall coverage summary."""

    covered_lines: int
    missing_lines: int
    excluded_lines: int
    percent_covered: float
    num_files: int


class CoverageCollectEvent(BaseEvent):
    """Event for coverage statistics collection."""

    type: Literal['collect.coverage'] = 'collect.coverage'
    summary: CoverageSummary
    files: list[CoverageFileSummary]
    duration_seconds: float
