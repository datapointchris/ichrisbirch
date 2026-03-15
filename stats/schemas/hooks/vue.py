"""Vue frontend hook schemas — vue-eslint, vue-prettier, vue-typecheck."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class EslintMessage(BaseModel):
    """A single ESLint message (error or warning)."""

    rule_id: str | None = None
    severity: int
    message: str
    line: int
    column: int
    file: str


class VueEslintHookEvent(BaseEvent):
    """Event for vue-eslint hook — captures ESLint errors and warnings."""

    type: Literal['hook.vue-eslint'] = 'hook.vue-eslint'
    status: Literal['passed', 'failed']
    exit_code: int
    error_count: int
    warning_count: int
    fixable_error_count: int
    fixable_warning_count: int
    messages: list[EslintMessage]
    files_checked: list[str]
    duration_seconds: float


class VuePrettierHookEvent(BaseEvent):
    """Event for vue-prettier hook — tracks files reformatted."""

    type: Literal['hook.vue-prettier'] = 'hook.vue-prettier'
    status: Literal['passed', 'failed']
    exit_code: int
    files_reformatted: list[str]
    files_checked: list[str]
    duration_seconds: float


class TypecheckError(BaseModel):
    """A single TypeScript type error."""

    file: str
    line: int
    column: int
    code: str
    message: str


class VueTypecheckHookEvent(BaseEvent):
    """Event for vue-typecheck hook — captures TypeScript type errors."""

    type: Literal['hook.vue-typecheck'] = 'hook.vue-typecheck'
    status: Literal['passed', 'failed']
    exit_code: int
    error_count: int
    errors: list[TypecheckError]
    duration_seconds: float
