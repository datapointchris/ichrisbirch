"""Terraform fmt hook runner - checks if .tf files need reformatting."""

from __future__ import annotations

import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.terraform import TerraformFmtHookEvent


def run(staged_files: list[str], branch: str, project: str) -> TerraformFmtHookEvent:
    """Run terraform fmt -check on staged .tf files, return fully-typed event.

    terraform fmt -check outputs filenames that would be reformatted, one per line.

    Args:
        staged_files: List of file paths to check
        branch: Current git branch
        project: Project name

    Returns:
        TerraformFmtHookEvent with reformatting results
    """
    start_time = time.perf_counter()

    tf_files = [f for f in staged_files if f.endswith('.tf')]

    if not tf_files:
        return TerraformFmtHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            files_reformatted=[],
            files_checked=[],
            duration_seconds=0.0,
        )

    result = subprocess.run(  # nosec B603 B607
        ['terraform', 'fmt', '-check', '-diff', *tf_files],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time

    # terraform fmt -check outputs filenames that need reformatting, one per line
    files_reformatted = [line for line in result.stdout.strip().splitlines() if line.strip()]

    return TerraformFmtHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        files_reformatted=files_reformatted,
        files_checked=tf_files,
        duration_seconds=round(duration, 3),
    )
