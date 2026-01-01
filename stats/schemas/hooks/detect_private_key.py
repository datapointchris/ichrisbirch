"""Detect-private-key hook event schema - captures secret detection results."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class DetectedPrivateKey(BaseModel):
    """A detected private key file."""

    path: str
    key_type: str | None = None


class DetectPrivateKeyHookEvent(BaseEvent):
    """Event for detect-private-key security hook."""

    type: Literal['hook.detect-private-key'] = 'hook.detect-private-key'
    status: Literal['passed', 'failed']
    exit_code: int
    issues: list[DetectedPrivateKey]
    files_checked: list[str]
    duration_seconds: float
