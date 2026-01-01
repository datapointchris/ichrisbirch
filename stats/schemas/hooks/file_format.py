"""File format validation hook schemas - check-yaml, check-toml, check-json."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class FileFormatIssue(BaseModel):
    """A file format validation issue."""

    path: str
    line: int | None
    column: int | None
    message: str


class CheckYamlHookEvent(BaseEvent):
    """Event for check-yaml file format validation hook."""

    type: Literal['hook.check-yaml'] = 'hook.check-yaml'
    status: Literal['passed', 'failed']
    exit_code: int
    issues: list[FileFormatIssue]
    files_checked: list[str]
    duration_seconds: float


class CheckTomlHookEvent(BaseEvent):
    """Event for check-toml file format validation hook."""

    type: Literal['hook.check-toml'] = 'hook.check-toml'
    status: Literal['passed', 'failed']
    exit_code: int
    issues: list[FileFormatIssue]
    files_checked: list[str]
    duration_seconds: float


class CheckJsonHookEvent(BaseEvent):
    """Event for check-json file format validation hook."""

    type: Literal['hook.check-json'] = 'hook.check-json'
    status: Literal['passed', 'failed']
    exit_code: int
    issues: list[FileFormatIssue]
    files_checked: list[str]
    duration_seconds: float
