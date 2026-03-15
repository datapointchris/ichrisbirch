"""Docker Compose validate hook runner - validates compose file syntax."""

from __future__ import annotations

import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.docker import DockerComposeValidateHookEvent


def run(staged_files: list[str], branch: str, project: str) -> DockerComposeValidateHookEvent:
    """Run docker compose config validation on staged compose files.

    Args:
        staged_files: List of file paths to check
        branch: Current git branch
        project: Project name

    Returns:
        DockerComposeValidateHookEvent with validation results
    """
    start_time = time.perf_counter()

    compose_files = [f for f in staged_files if f.rsplit('/', 1)[-1].startswith('docker-compose') and f.endswith('.yml')]

    if not compose_files:
        return DockerComposeValidateHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            files_checked=[],
            duration_seconds=0.0,
        )

    worst_exit_code = 0

    for compose_file in compose_files:
        result = subprocess.run(  # nosec B603 B607
            ['docker', 'compose', '-f', compose_file, 'config', '--quiet'],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            worst_exit_code = result.returncode

    duration = time.perf_counter() - start_time

    return DockerComposeValidateHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if worst_exit_code == 0 else 'failed',
        exit_code=worst_exit_code,
        files_checked=compose_files,
        duration_seconds=round(duration, 3),
    )
