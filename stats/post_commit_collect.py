#!/usr/bin/env python
"""Post-commit hook: collect stats from configured collectors."""

from __future__ import annotations

import subprocess  # nosec B404
import sys
import time
from datetime import UTC
from datetime import datetime
from pathlib import Path

from stats.collectors import discover_collectors
from stats.collectors import get_collector
from stats.config import load_config
from stats.emit import emit_event
from stats.schemas.commit import CommitEvent
from stats.schemas.commit import StagedFile

TIMING_DIR = Path(__file__).parent / 'timing'


def write_timing(collector_name: str, duration: float, total_duration: float | None = None) -> None:
    """Append timing entry to collect timing log."""
    TIMING_DIR.mkdir(exist_ok=True)
    log_file = TIMING_DIR / 'collect.log'
    timestamp = datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')

    with log_file.open('a') as f:
        if total_duration is not None:
            f.write(f'{timestamp} | TOTAL | {total_duration:.3f}s\n')
        else:
            f.write(f'{timestamp} | {collector_name} | {duration:.3f}s\n')


def get_branch() -> str:
    """Get current git branch."""
    result = subprocess.run(  # nosec B603 B607
        ['git', 'branch', '--show-current'],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() or 'HEAD'


def get_commit_info() -> dict:
    """Get info about the commit that just happened."""
    result = subprocess.run(  # nosec B603 B607
        ['git', 'log', '-1', '--format=%H|%h|%s|%an|%ae|%aI'],
        capture_output=True,
        text=True,
    )
    parts = result.stdout.strip().split('|')

    stat_result = subprocess.run(  # nosec B603 B607
        ['git', 'diff', '--stat', '--stat-count=1000', 'HEAD~1..HEAD'],
        capture_output=True,
        text=True,
    )

    stat_lines = stat_result.stdout.strip().split('\n')
    insertions = 0
    deletions = 0
    files_changed = 0

    if stat_lines:
        summary = stat_lines[-1]
        if 'insertion' in summary:
            try:
                insertions = int(summary.split('insertion')[0].split(',')[-1].strip())
            except (ValueError, IndexError):
                insertions = 0
        if 'deletion' in summary:
            try:
                deletions = int(summary.split('deletion')[0].split(',')[-1].strip())
            except (ValueError, IndexError):
                deletions = 0
        if 'file' in summary:
            try:
                files_changed = int(summary.split('file')[0].strip())
            except (ValueError, IndexError):
                files_changed = 0

    return {
        'hash': parts[0] if parts else '',
        'short_hash': parts[1] if len(parts) > 1 else '',
        'message': parts[2] if len(parts) > 2 else '',
        'author': parts[3] if len(parts) > 3 else '',
        'email': parts[4] if len(parts) > 4 else '',
        'timestamp': parts[5] if len(parts) > 5 else '',
        'files_changed': files_changed,
        'insertions': insertions,
        'deletions': deletions,
    }


def get_staged_files_from_commit() -> list[StagedFile]:
    """Get files that were in the commit with their stats."""
    result = subprocess.run(  # nosec B603 B607
        ['git', 'diff', '--numstat', 'HEAD~1..HEAD'],
        capture_output=True,
        text=True,
    )

    files = []
    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) >= 3:
            added = int(parts[0]) if parts[0] != '-' else 0
            removed = int(parts[1]) if parts[1] != '-' else 0
            path = parts[2]

            if added > 0 and removed == 0:
                status = 'added'
            elif removed > 0 and added == 0:
                status = 'deleted'
            else:
                status = 'modified'

            files.append(
                StagedFile(
                    path=path,
                    status=status,  # type: ignore[arg-type]
                    lines_added=added,
                    lines_removed=removed,
                )
            )

    return files


def main() -> int:
    """Run post-commit collection."""
    total_start = time.perf_counter()

    config = load_config()
    project = config['project']
    events_path = config['events_path']
    branch = get_branch()
    commit_info = get_commit_info()

    commit_timestamp = datetime.fromisoformat(commit_info['timestamp'])

    staged_files = get_staged_files_from_commit()

    commit_event = CommitEvent(
        timestamp=commit_timestamp,
        project=project,
        branch=branch,
        hash=commit_info['hash'],
        short_hash=commit_info['short_hash'],
        message=commit_info['message'],
        author=commit_info['author'],
        email=commit_info['email'],
        files_changed=commit_info['files_changed'],
        insertions=commit_info['insertions'],
        deletions=commit_info['deletions'],
        staged_files=staged_files,
    )
    emit_event(commit_event, events_path)

    enabled_collectors = config.get('collect', {}).get('collectors', [])
    available_collectors = discover_collectors()
    collect_config = config.get('collect', {})

    for collector_name in enabled_collectors:
        if collector_name not in available_collectors:
            print(f"Warning: Unknown collector '{collector_name}', skipping")
            continue

        collector_runner = get_collector(collector_name)
        if collector_runner is not None:
            try:
                start = time.perf_counter()
                if collector_name == 'pytest_collector':
                    json_path = collect_config.get('pytest_json_path', '/tmp/ichrisbirch-pytest-report.json')  # nosec B108
                    event = collector_runner(branch, project, json_path)
                elif collector_name == 'coverage':
                    event = collector_runner(branch, project)
                else:
                    event = collector_runner(branch, project)
                duration = time.perf_counter() - start
                write_timing(collector_name, duration)

                if event is not None:
                    emit_event(event, events_path)
            except Exception as e:
                print(f"Warning: Collector '{collector_name}' failed: {e}")

    total_duration = time.perf_counter() - total_start
    write_timing('', 0, total_duration)

    return 0


if __name__ == '__main__':
    sys.exit(main())
