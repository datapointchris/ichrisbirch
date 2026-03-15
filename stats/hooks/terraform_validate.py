"""Terraform validate hook runner - runs terraform validate in directories with staged .tf files."""

from __future__ import annotations

import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime
from pathlib import Path

from stats.schemas.hooks.terraform import TerraformValidateHookEvent


def run(staged_files: list[str], branch: str, project: str) -> TerraformValidateHookEvent:
    """Run terraform validate on staged .tf files, return fully-typed event.

    Runs terraform validate -json in each unique directory containing staged .tf files.
    Status is 'failed' if any directory fails validation.

    Args:
        staged_files: List of file paths to check
        branch: Current git branch
        project: Project name

    Returns:
        TerraformValidateHookEvent with validation results
    """
    start_time = time.perf_counter()

    tf_files = [f for f in staged_files if f.endswith('.tf')]

    if not tf_files:
        return TerraformValidateHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            files_checked=[],
            duration_seconds=0.0,
        )

    # Get unique directories containing .tf files
    directories = sorted({str(Path(f).parent) for f in tf_files})

    overall_exit_code = 0
    for directory in directories:
        result = subprocess.run(  # nosec B603 B607
            ['terraform', 'validate', '-json'],
            capture_output=True,
            text=True,
            cwd=directory,
        )
        if result.returncode != 0:
            overall_exit_code = result.returncode

    duration = time.perf_counter() - start_time

    return TerraformValidateHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if overall_exit_code == 0 else 'failed',
        exit_code=overall_exit_code,
        files_checked=tf_files,
        duration_seconds=round(duration, 3),
    )
