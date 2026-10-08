"""Code-sync hook runner - captures mkdocs code-sync validation."""

from __future__ import annotations

import datetime as dt
import subprocess  # nosec B404
import time

from stats.schemas.hooks.project import CodeSyncHookEvent


def run(staged_files: list[str], branch: str, project: str) -> CodeSyncHookEvent:
    """Run code-sync on all staged files, return fully-typed event.

    This hook always runs regardless of which files are staged (always_run: true
    in pre-commit config), so staged_files are not filtered.
    """
    start_time = time.perf_counter()

    result = subprocess.run(  # nosec B603 B607
        ['uv', 'run', 'python', '-m', 'mkdocs_plugins.code_sync', 'docs', '--base-path', '.'],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time

    return CodeSyncHookEvent(
        timestamp=dt.datetime.now(dt.UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        files_checked=staged_files,
        duration_seconds=round(duration, 3),
    )
