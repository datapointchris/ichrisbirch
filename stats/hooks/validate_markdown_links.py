"""Validate-markdown-links hook runner - captures broken link issues."""

from __future__ import annotations

import re
import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.validate_markdown_links import BrokenLink
from stats.schemas.hooks.validate_markdown_links import ValidateMarkdownLinksHookEvent

# Pattern: filepath:line: broken link 'url'
BROKEN_LINK_PATTERN = re.compile(r"^(?P<path>.+?):(?P<line>\d+): broken link '(?P<link>.+)'$")


def run(staged_files: list[str], branch: str, project: str) -> ValidateMarkdownLinksHookEvent:
    """Run validate-markdown-links on staged files, return fully-typed event."""
    start_time = time.perf_counter()

    if not staged_files:
        return ValidateMarkdownLinksHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            broken_links=[],
            files_checked=[],
            duration_seconds=0.0,
        )

    # Filter to only markdown files
    md_files = [f for f in staged_files if f.endswith('.md')]

    if not md_files:
        return ValidateMarkdownLinksHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            broken_links=[],
            files_checked=[],
            duration_seconds=0.0,
        )

    result = subprocess.run(  # nosec B603 B607
        ['python', 'scripts/pre_commit_validations/validate_markdown_links.py', *md_files],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time
    broken_links = _parse_output(result.stdout + result.stderr)

    return ValidateMarkdownLinksHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        broken_links=broken_links,
        files_checked=md_files,
        duration_seconds=round(duration, 3),
    )


def _parse_output(output: str) -> list[BrokenLink]:
    """Parse validate-markdown-links output."""
    links: list[BrokenLink] = []

    for line in output.split('\n'):
        line = line.strip()
        match = BROKEN_LINK_PATTERN.match(line)
        if match:
            links.append(
                BrokenLink(
                    path=match.group('path'),
                    line=int(match.group('line')),
                    link=match.group('link'),
                )
            )

    return links
