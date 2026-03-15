"""npm dependencies collector event schema — captures frontend package counts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class NpmDependency(BaseModel):
    """A single npm dependency."""

    name: str
    version: str


class NpmDependenciesCollectEvent(BaseEvent):
    """Event for npm dependency collection from package-lock.json."""

    type: Literal['collect.npm_dependencies'] = 'collect.npm_dependencies'
    production_count: int
    dev_count: int
    total_count: int
    production_dependencies: list[NpmDependency]
    dev_dependencies: list[NpmDependency]
    duration_seconds: float
