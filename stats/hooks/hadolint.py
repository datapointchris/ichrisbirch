"""Hadolint hook runner - captures Dockerfile linting issues with full details."""

from __future__ import annotations

import json
import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.docker import HadolintHookEvent
from stats.schemas.hooks.docker import HadolintIssue


def run(staged_files: list[str], branch: str, project: str) -> HadolintHookEvent:
    """Run hadolint on staged Dockerfiles, return fully-typed event.

    Args:
        staged_files: List of file paths to check
        branch: Current git branch
        project: Project name

    Returns:
        HadolintHookEvent with full issue details
    """
    start_time = time.perf_counter()

    dockerfiles = [f for f in staged_files if _is_dockerfile(f.rsplit('/', 1)[-1])]

    if not dockerfiles:
        return HadolintHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            issues=[],
            files_checked=[],
            duration_seconds=0.0,
        )

    result = subprocess.run(  # nosec B603 B607
        ['hadolint', '--format', 'json', *dockerfiles],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time

    raw_issues: list[dict] = []
    if result.stdout.strip():
        try:
            raw_issues = json.loads(result.stdout)
        except json.JSONDecodeError:
            raw_issues = []

    issues = [
        HadolintIssue(
            code=item['code'],
            message=item['message'],
            level=item['level'],
            file=item['file'],
            line=item['line'],
            column=item['column'],
        )
        for item in raw_issues
    ]

    return HadolintHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        issues=issues,
        files_checked=dockerfiles,
        duration_seconds=round(duration, 3),
    )


def _is_dockerfile(filename: str) -> bool:
    """Check if a filename is a Dockerfile variant.

    Matches: Dockerfile, Dockerfile.prod, Dockerfile.dev, foo.dockerfile
    """
    return filename == 'Dockerfile' or filename.startswith('Dockerfile.') or filename.endswith('.dockerfile')
