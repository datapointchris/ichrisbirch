"""Shellcheck hook runner - captures ALL shellcheck output with full details."""

from __future__ import annotations

import json
import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.shellcheck import ShellcheckComment
from stats.schemas.hooks.shellcheck import ShellcheckFix
from stats.schemas.hooks.shellcheck import ShellcheckHookEvent
from stats.schemas.hooks.shellcheck import ShellcheckReplacement


def run(staged_files: list[str], branch: str, project: str) -> ShellcheckHookEvent:
    """Run shellcheck on staged files, return fully-typed event.

    Args:
        staged_files: List of file paths to check
        branch: Current git branch
        project: Project name

    Returns:
        ShellcheckHookEvent with full comment details
    """
    start_time = time.perf_counter()

    # Filter to only shell files
    shell_files = [f for f in staged_files if f.endswith('.sh')]

    if not shell_files:
        return ShellcheckHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            comments=[],
            files_checked=[],
            duration_seconds=0.0,
        )

    result = subprocess.run(  # nosec B603 B607
        ['shellcheck', '--format=json1', *shell_files],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time

    # Parse shellcheck JSON output
    raw_output: dict = {}
    if result.stdout.strip():
        try:
            raw_output = json.loads(result.stdout)
        except json.JSONDecodeError:
            raw_output = {}

    comments = [_parse_comment(c) for c in raw_output.get('comments', [])]

    return ShellcheckHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        comments=comments,
        files_checked=shell_files,
        duration_seconds=round(duration, 3),
    )


def _parse_comment(comment: dict) -> ShellcheckComment:
    """Parse a single shellcheck comment from JSON."""
    fix_data = comment.get('fix')
    fix = None
    if fix_data:
        replacements = [
            ShellcheckReplacement(
                column=r['column'],
                endColumn=r['endColumn'],
                endLine=r['endLine'],
                insertionPoint=r['insertionPoint'],
                line=r['line'],
                precedence=r['precedence'],
                replacement=r['replacement'],
            )
            for r in fix_data.get('replacements', [])
        ]
        fix = ShellcheckFix(replacements=replacements)

    return ShellcheckComment(
        file=comment['file'],
        line=comment['line'],
        endLine=comment['endLine'],
        column=comment['column'],
        endColumn=comment['endColumn'],
        level=comment['level'],
        code=comment['code'],
        message=comment['message'],
        fix=fix,
    )
