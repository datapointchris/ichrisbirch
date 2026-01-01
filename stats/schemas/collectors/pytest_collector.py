"""Pytest collector event schema - captures test results from pytest-json-report."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class PytestPhase(BaseModel):
    """A single phase of a test (setup/call/teardown)."""

    outcome: Literal['passed', 'failed', 'skipped', 'error']
    duration: float
    longrepr: str | None = None


class PytestTest(BaseModel):
    """A single test result."""

    nodeid: str
    outcome: Literal['passed', 'failed', 'skipped', 'error']
    duration: float
    setup: PytestPhase | None = None
    call: PytestPhase | None = None
    teardown: PytestPhase | None = None


class PytestSummary(BaseModel):
    """Summary of test results."""

    passed: int = 0
    failed: int = 0
    skipped: int = 0
    error: int = 0
    total: int = 0
    collected: int = 0


class PytestCollectEvent(BaseEvent):
    """Event for pytest test results collection."""

    type: Literal['collect.pytest'] = 'collect.pytest'
    summary: PytestSummary
    tests: list[PytestTest]
    duration_seconds: float
    exit_code: int
