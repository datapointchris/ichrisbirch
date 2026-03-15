"""Docker hook schemas — docker-compose-validate, hadolint."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class DockerComposeValidateHookEvent(BaseEvent):
    """Event for docker-compose-validate hook."""

    type: Literal['hook.docker-compose-validate'] = 'hook.docker-compose-validate'
    status: Literal['passed', 'failed']
    exit_code: int
    files_checked: list[str]
    duration_seconds: float


class HadolintIssue(BaseModel):
    """A single hadolint warning or error."""

    code: str
    message: str
    level: str
    file: str
    line: int
    column: int


class HadolintHookEvent(BaseEvent):
    """Event for hadolint Dockerfile linter hook."""

    type: Literal['hook.hadolint'] = 'hook.hadolint'
    status: Literal['passed', 'failed']
    exit_code: int
    issues: list[HadolintIssue]
    files_checked: list[str]
    duration_seconds: float
