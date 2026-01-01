"""Detect-private-key hook runner - captures private key detection results."""

from __future__ import annotations

import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime

from stats.schemas.hooks.detect_private_key import DetectedPrivateKey
from stats.schemas.hooks.detect_private_key import DetectPrivateKeyHookEvent


def run(staged_files: list[str], branch: str, project: str) -> DetectPrivateKeyHookEvent:
    """Run detect-private-key on staged files, return fully-typed event.

    Args:
        staged_files: List of file paths to check
        branch: Current git branch
        project: Project name

    Returns:
        DetectPrivateKeyHookEvent with detected private keys
    """
    start_time = time.perf_counter()

    if not staged_files:
        return DetectPrivateKeyHookEvent(
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
        ['uvx', '--from', 'pre-commit-hooks', 'detect-private-key', *staged_files],
        capture_output=True,
        text=True,
    )

    duration = time.perf_counter() - start_time
    issues = _parse_output(result.stdout + result.stderr)

    return DetectPrivateKeyHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        issues=issues,
        files_checked=staged_files,
        duration_seconds=round(duration, 3),
    )


def _parse_output(output: str) -> list[DetectedPrivateKey]:
    """Parse detect-private-key output for detected files.

    Output format: "Private key found: <filepath>"
    """
    issues: list[DetectedPrivateKey] = []

    for line in output.split('\n'):
        line = line.strip()
        if not line:
            continue

        if line.startswith('Private key found:'):
            path = line.replace('Private key found:', '').strip()
            issues.append(DetectedPrivateKey(path=path))

    return issues
