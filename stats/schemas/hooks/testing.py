"""Pre-commit test gate hook schemas — pytest-affected, pytest-full."""

from __future__ import annotations

from typing import Literal

from stats.schemas.base import BaseEvent


class PytestAffectedHookEvent(BaseEvent):
    """Event for pytest-affected hook — execution metadata only."""

    type: Literal['hook.pytest-affected'] = 'hook.pytest-affected'
    status: Literal['passed', 'failed', 'skipped']
    exit_code: int
    tests_selected: int
    duration_seconds: float


class PytestFullHookEvent(BaseEvent):
    """Event for pytest-full hook — execution metadata only."""

    type: Literal['hook.pytest-full'] = 'hook.pytest-full'
    status: Literal['passed', 'failed', 'skipped']
    exit_code: int
    tests_run: int
    duration_seconds: float
