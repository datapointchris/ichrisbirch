"""Vitest collector event schema — captures Vue/TS test results from vitest JSON reporter."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class VitestTest(BaseModel):
    """A single vitest test result."""

    name: str
    suite: str
    outcome: Literal['passed', 'failed', 'skipped']
    duration: float


class VitestSummary(BaseModel):
    """Summary of vitest test results."""

    passed: int = 0
    failed: int = 0
    skipped: int = 0
    total: int = 0


class VitestCollectEvent(BaseEvent):
    """Event for vitest test results collection."""

    type: Literal['collect.vitest'] = 'collect.vitest'
    summary: VitestSummary
    tests: list[VitestTest]
    duration_seconds: float
    exit_code: int
