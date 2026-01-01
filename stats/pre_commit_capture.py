#!/usr/bin/env python
"""Pre-commit hook: capture stats from configured hooks."""

from __future__ import annotations

import subprocess  # nosec B404
import sys
import time
from datetime import UTC
from datetime import datetime
from pathlib import Path

from stats.config import load_config
from stats.emit import emit_event
from stats.hooks import discover_hooks
from stats.hooks import get_hook

TIMING_DIR = Path(__file__).parent / 'timing'


def get_staged_files() -> list[str]:
    """Get list of staged files."""
    result = subprocess.run(  # nosec B603 B607
        ['git', 'diff', '--cached', '--name-only'],
        capture_output=True,
        text=True,
    )
    return [f for f in result.stdout.strip().split('\n') if f]


def get_branch() -> str:
    """Get current git branch."""
    result = subprocess.run(  # nosec B603 B607
        ['git', 'branch', '--show-current'],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() or 'HEAD'


def write_timing(hook_name: str, duration: float, total_duration: float | None = None) -> None:
    """Append timing entry to capture timing log."""
    TIMING_DIR.mkdir(exist_ok=True)
    log_file = TIMING_DIR / 'capture.log'
    timestamp = datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')

    with log_file.open('a') as f:
        if total_duration is not None:
            f.write(f'{timestamp} | TOTAL | {total_duration:.3f}s\n')
        else:
            f.write(f'{timestamp} | {hook_name} | {duration:.3f}s\n')


def main() -> int:
    """Run pre-commit capture."""
    total_start = time.perf_counter()

    config = load_config()
    project = config['project']
    events_path = config['events_path']
    staged_files = get_staged_files()
    branch = get_branch()

    if not staged_files:
        return 0

    enabled_hooks = config.get('capture', {}).get('hooks', [])
    available_hooks = discover_hooks()

    for hook_name in enabled_hooks:
        if hook_name not in available_hooks:
            print(f"Warning: Unknown hook '{hook_name}', skipping")
            continue

        hook_runner = get_hook(hook_name)
        if hook_runner is not None:
            start = time.perf_counter()
            event = hook_runner(staged_files, branch, project)
            duration = time.perf_counter() - start
            write_timing(hook_name, duration)
            emit_event(event, events_path)

    total_duration = time.perf_counter() - total_start
    write_timing('', 0, total_duration)

    return 0


if __name__ == '__main__':
    sys.exit(main())
