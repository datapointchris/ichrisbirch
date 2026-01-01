"""Pyupgrade hook event schema - captures Python upgrade rewrites."""

from __future__ import annotations

from typing import Literal

from stats.schemas.base import BaseEvent


class PyupgradeHookEvent(BaseEvent):
    """Event for pyupgrade Python syntax upgrade hook.

    Pyupgrade modifies files in place to upgrade Python syntax.
    This event tracks which files were rewritten.
    """

    type: Literal['hook.pyupgrade'] = 'hook.pyupgrade'
    status: Literal['passed', 'failed']
    exit_code: int
    rewritten_files: list[str]  # Files that were modified by pyupgrade
    files_checked: list[str]
    duration_seconds: float
