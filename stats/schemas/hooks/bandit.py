"""Bandit hook event schema - captures ALL bandit output."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from stats.schemas.base import BaseEvent


class BanditCWE(BaseModel):
    """CWE reference for a bandit issue."""

    id: int
    link: str


class BanditIssue(BaseModel):
    """Full bandit issue with all fields."""

    code: str
    col_offset: int
    end_col_offset: int
    filename: str
    issue_confidence: Literal['HIGH', 'MEDIUM', 'LOW', 'UNDEFINED']
    issue_cwe: BanditCWE | None = None
    issue_severity: Literal['HIGH', 'MEDIUM', 'LOW', 'UNDEFINED']
    issue_text: str
    line_number: int
    line_range: list[int]
    more_info: str
    test_id: str
    test_name: str


class BanditMetrics(BaseModel):
    """Bandit scan metrics."""

    confidence_high: int = 0
    confidence_medium: int = 0
    confidence_low: int = 0
    confidence_undefined: int = 0
    severity_high: int = 0
    severity_medium: int = 0
    severity_low: int = 0
    severity_undefined: int = 0
    loc: int = 0
    nosec: int = 0
    skipped_tests: int = 0


class BanditHookEvent(BaseEvent):
    """Event for bandit security scan hook."""

    type: Literal['hook.bandit'] = 'hook.bandit'
    status: Literal['passed', 'failed']
    exit_code: int
    issues: list[BanditIssue]
    metrics: BanditMetrics
    files_checked: list[str]
    duration_seconds: float
