"""Playwright collector event schema — captures E2E test results from Playwright JSON reporter."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class PlaywrightTest(BaseModel):
    """A single Playwright E2E test result."""

    name: str
    suite: str
    outcome: str
    duration: float


class PlaywrightSummary(BaseModel):
    """Summary of Playwright test results."""

    passed: int = 0
    failed: int = 0
    skipped: int = 0
    total: int = 0


class PlaywrightCollectEvent(BaseEvent):
    """Event for Playwright E2E test results collection."""

    type: Literal['collect.playwright'] = 'collect.playwright'
    summary: PlaywrightSummary
    tests: list[PlaywrightTest]
    duration_seconds: float
    exit_code: int
