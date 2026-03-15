"""Vue ESLint hook runner - captures ESLint errors and warnings from Vue/TS files."""

from __future__ import annotations

import json
import re
import subprocess  # nosec B404
import time
from datetime import UTC
from datetime import datetime
from pathlib import Path

from stats.schemas.hooks.vue import EslintMessage
from stats.schemas.hooks.vue import VueEslintHookEvent

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / 'frontend'
VUE_FILE_PATTERN = re.compile(r'^frontend/.*\.(vue|js|ts|jsx|tsx)$')


def run(staged_files: list[str], branch: str, project: str) -> VueEslintHookEvent:
    """Run ESLint on staged Vue/TS files, return fully-typed event."""
    start_time = time.perf_counter()

    vue_files = [f for f in staged_files if VUE_FILE_PATTERN.match(f)]

    if not vue_files:
        return VueEslintHookEvent(
            timestamp=datetime.now(UTC),
            project=project,
            branch=branch,
            status='passed',
            exit_code=0,
            error_count=0,
            warning_count=0,
            fixable_error_count=0,
            fixable_warning_count=0,
            messages=[],
            files_checked=[],
            duration_seconds=0.0,
        )

    result = subprocess.run(  # nosec B603 B607
        ['npm', 'run', 'lint', '--', '--format', 'json'],
        capture_output=True,
        text=True,
        cwd=FRONTEND_DIR,
    )

    duration = time.perf_counter() - start_time

    eslint_results = _extract_eslint_json(result.stdout)

    total_errors = 0
    total_warnings = 0
    total_fixable_errors = 0
    total_fixable_warnings = 0
    messages: list[EslintMessage] = []

    for file_result in eslint_results:
        total_errors += file_result.get('errorCount', 0)
        total_warnings += file_result.get('warningCount', 0)
        total_fixable_errors += file_result.get('fixableErrorCount', 0)
        total_fixable_warnings += file_result.get('fixableWarningCount', 0)

        file_path = file_result.get('filePath', '')
        for msg in file_result.get('messages', []):
            messages.append(
                EslintMessage(
                    rule_id=msg.get('ruleId'),
                    severity=msg.get('severity', 0),
                    message=msg.get('message', ''),
                    line=msg.get('line', 0),
                    column=msg.get('column', 0),
                    file=file_path,
                )
            )

    return VueEslintHookEvent(
        timestamp=datetime.now(UTC),
        project=project,
        branch=branch,
        status='passed' if result.returncode == 0 else 'failed',
        exit_code=result.returncode,
        error_count=total_errors,
        warning_count=total_warnings,
        fixable_error_count=total_fixable_errors,
        fixable_warning_count=total_fixable_warnings,
        messages=messages,
        files_checked=vue_files,
        duration_seconds=round(duration, 3),
    )


def _extract_eslint_json(output: str) -> list[dict]:
    """Extract ESLint JSON array from potentially mixed npm output.

    ESLint's --format json produces a top-level JSON array, but npm may
    prepend/append its own output lines. We scan for the outermost [...].
    """
    # Try parsing the entire output first
    stripped = output.strip()
    if stripped.startswith('['):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass

    # Look for a JSON array embedded in the output
    bracket_start = output.find('[')
    if bracket_start == -1:
        return []

    # Find the matching closing bracket by tracking nesting
    depth = 0
    for i in range(bracket_start, len(output)):
        if output[i] == '[':
            depth += 1
        elif output[i] == ']':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(output[bracket_start : i + 1])
                except json.JSONDecodeError:
                    return []

    return []
