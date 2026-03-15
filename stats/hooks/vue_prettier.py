"""Vue Prettier hook runner - detects files that need reformatting."""

from __future__ import annotations

import re
import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime
from pathlib import Path

from stats.schemas.hooks.vue import VuePrettierHookEvent

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / 'frontend'
VUE_FILE_PATTERN = re.compile(r'^frontend/.*\.(vue|js|ts|jsx|tsx|css|scss|json|md)$')


def run(staged_files: list[str], branch: str, project: str) -> VuePrettierHookEvent:
    """Run Prettier check on staged files, return fully-typed event."""
    start_time = time.perf_counter()

    vue_files = [f for f in staged_files if VUE_FILE_PATTERN.match(f)]

    if not vue_files:
        return VuePrettierHookEvent(
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
        ['npx', 'prettier', '--check', 'src/'],
        capture_output=True,
        text=True,
        cwd=FRONTEND_DIR,
    )

    duration = time.perf_counter() - start_time

    unformatted_files = _parse_prettier_output(result.stdout + result.stderr)

    return VuePrettierHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        files_reformatted=unformatted_files,
        files_checked=vue_files,
        duration_seconds=round(duration, 3),
    )


def _parse_prettier_output(output: str) -> list[str]:
    """Parse Prettier --check output for files that need formatting.

    Prettier outputs lines like:
        Checking formatting...
        [warn] src/components/Foo.vue
        [warn] Code style issues found in the above file(s).
    """
    unformatted: list[str] = []

    for line in output.split('\n'):
        line = line.strip()
        # Skip empty lines, status messages, and summary lines
        if not line:
            continue
        if line.startswith('Checking formatting'):
            continue
        if 'Code style issues' in line:
            continue
        if line.startswith('All matched files'):
            continue

        # Strip [warn] prefix if present
        if line.startswith('[warn] '):
            path = line[7:]
        else:
            path = line

        # Keep lines that look like file paths (contain a dot and slash)
        if '/' in path and '.' in path:
            unformatted.append(path)

    return unformatted
