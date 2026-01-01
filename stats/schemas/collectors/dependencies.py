"""Dependencies collector event schema - captures Python dependencies."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class Dependency(BaseModel):
    """A single Python dependency."""

    name: str
    version: str


class DependenciesCollectEvent(BaseEvent):
    """Event for Python dependencies collection."""

    type: Literal['collect.dependencies'] = 'collect.dependencies'
    dependencies: list[Dependency]
    total_count: int
    duration_seconds: float
