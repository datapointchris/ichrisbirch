"""Test fixtures for stats module tests.

All fixtures load real tool outputs captured from actual tool runs.
This ensures tests validate against realistic data structures.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

FIXTURES_DIR = Path(__file__).parent / 'fixtures' / 'tool_outputs'


@pytest.fixture
def ruff_clean_output() -> list[dict[str, Any]]:
    """Load clean ruff output (no issues)."""
    return json.loads((FIXTURES_DIR / 'ruff_clean.json').read_text())


@pytest.fixture
def ruff_with_issues_output() -> list[dict[str, Any]]:
    """Load ruff output with issues."""
    return json.loads((FIXTURES_DIR / 'ruff_with_issues.json').read_text())


@pytest.fixture
def mypy_clean_output() -> str:
    """Load clean mypy output."""
    return (FIXTURES_DIR / 'mypy_clean.txt').read_text()


@pytest.fixture
def bandit_with_issues_output() -> dict[str, Any]:
    """Load bandit output with issues."""
    return json.loads((FIXTURES_DIR / 'bandit_with_issues.json').read_text())


@pytest.fixture
def tokei_output() -> dict[str, Any]:
    """Load tokei output."""
    return json.loads((FIXTURES_DIR / 'tokei_output.json').read_text())


@pytest.fixture
def docker_images_output() -> list[dict[str, Any]]:
    """Load docker images output (JSONL format)."""
    lines = (FIXTURES_DIR / 'docker_images.jsonl').read_text().strip().split('\n')
    return [json.loads(line) for line in lines if line]
