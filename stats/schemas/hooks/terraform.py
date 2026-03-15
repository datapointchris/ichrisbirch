"""Terraform hook schemas — terraform_validate, terraform_tflint, terraform_fmt, terraform_docs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class TerraformValidateHookEvent(BaseEvent):
    """Event for terraform_validate hook."""

    type: Literal['hook.terraform-validate'] = 'hook.terraform-validate'
    status: Literal['passed', 'failed']
    exit_code: int
    files_checked: list[str]
    duration_seconds: float


class TflintIssue(BaseModel):
    """A single tflint issue."""

    rule: str
    message: str
    severity: str
    file: str | None = None
    line: int | None = None


class TerraformTflintHookEvent(BaseEvent):
    """Event for terraform_tflint hook — captures lint issues."""

    type: Literal['hook.terraform-tflint'] = 'hook.terraform-tflint'
    status: Literal['passed', 'failed']
    exit_code: int
    issues: list[TflintIssue]
    files_checked: list[str]
    duration_seconds: float


class TerraformFmtHookEvent(BaseEvent):
    """Event for terraform_fmt hook — tracks files reformatted."""

    type: Literal['hook.terraform-fmt'] = 'hook.terraform-fmt'
    status: Literal['passed', 'failed']
    exit_code: int
    files_reformatted: list[str]
    files_checked: list[str]
    duration_seconds: float


class TerraformDocsHookEvent(BaseEvent):
    """Event for terraform_docs hook."""

    type: Literal['hook.terraform-docs'] = 'hook.terraform-docs'
    status: Literal['passed', 'failed']
    exit_code: int
    files_checked: list[str]
    duration_seconds: float
