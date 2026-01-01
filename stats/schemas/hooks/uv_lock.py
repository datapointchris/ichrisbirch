"""UV lock hook schema."""

from __future__ import annotations

from typing import Literal

from stats.schemas.base import BaseEvent


class UvLockHookEvent(BaseEvent):
    """Event for uv-lock dependency lock hook."""

    type: Literal['hook.uv-lock'] = 'hook.uv-lock'
    status: Literal['passed', 'failed']
    exit_code: int
    packages_resolved: int | None
    resolution_time_ms: int | None
    files_checked: list[str]
    duration_seconds: float
