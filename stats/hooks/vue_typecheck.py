"""Vue TypeScript type-check hook runner - captures tsc type errors."""

from __future__ import annotations

import re
import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime
from pathlib import Path

from stats.schemas.hooks.vue import TypecheckError
from stats.schemas.hooks.vue import VueTypecheckHookEvent

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / 'frontend'
VUE_FILE_PATTERN = re.compile(r'^frontend/.*\.(vue|ts|tsx)$')

# tsc error format: src/file.ts(10,5): error TS2322: Type 'string' is not assignable...
TSC_ERROR_PATTERN = re.compile(r'^(.+?)\((\d+),(\d+)\):\s+error\s+(TS\d+):\s+(.+)$')


def run(staged_files: list[str], branch: str, project: str) -> VueTypecheckHookEvent:
    """Run vue-tsc type checking on staged files, return fully-typed event."""
    start_time = time.perf_counter()

    vue_files = [f for f in staged_files if VUE_FILE_PATTERN.match(f)]

    if not vue_files:
        return VueTypecheckHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            error_count=0,
            errors=[],
            duration_seconds=0.0,
        )

    result = subprocess.run(  # nosec B603 B607
        ['npm', 'run', 'typecheck'],
        capture_output=True,
        text=True,
        cwd=FRONTEND_DIR,
    )

    duration = time.perf_counter() - start_time

    errors = _parse_tsc_output(result.stdout + result.stderr)

    return VueTypecheckHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        error_count=len(errors),
        errors=errors,
        duration_seconds=round(duration, 3),
    )


def _parse_tsc_output(output: str) -> list[TypecheckError]:
    """Parse tsc output for type errors.

    Each error line looks like:
        src/file.ts(10,5): error TS2322: Type 'string' is not assignable to type 'number'.
    """
    errors: list[TypecheckError] = []

    for line in output.split('\n'):
        line = line.strip()
        match = TSC_ERROR_PATTERN.match(line)
        if match:
            errors.append(
                TypecheckError(
                    file=match.group(1),
                    line=int(match.group(2)),
                    column=int(match.group(3)),
                    code=match.group(4),
                    message=match.group(5),
                )
            )

    return errors
