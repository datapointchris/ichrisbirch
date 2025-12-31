#!/usr/bin/env python
"""Post-commit hook to collect and save project stats.

This script runs after a successful commit to:
1. Finalize the commit session (journey tracking)
2. Collect all project statistics
3. Save both to JSON files in stats/
4. Sync the stats directory with S3

The stats are tied to the current commit hash for tracking over time.
"""

from __future__ import annotations

import json
import subprocess
import sys
from contextlib import suppress
from datetime import UTC
from datetime import datetime
from pathlib import Path

from scripts.stats.collect import collect_all_stats
from scripts.stats.collect import display_stats
from scripts.stats.collect import save_stats
from scripts.stats.file_history import enrich_files
from scripts.stats.sync import push_stats

SESSION_DIR = Path('.tmp')
SESSIONS_OUTPUT_DIR = Path('stats/sessions')


def get_current_branch() -> str:
    """Get the current git branch name."""
    result = subprocess.run(
        ['git', 'branch', '--show-current'],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def get_session_file() -> Path:
    """Get session file path for current branch."""
    branch = get_current_branch()
    safe_branch = branch.replace('/', '-').replace('\\', '-')
    return SESSION_DIR / f'session-{safe_branch}.json'


def get_commit_info() -> dict:
    """Get info about the commit that was just made."""
    result = subprocess.run(
        ['git', 'log', '-1', '--format=%H|%h|%s|%an|%ae|%aI'],
        capture_output=True,
        text=True,
    )
    parts = result.stdout.strip().split('|')
    if len(parts) < 6:
        return {}

    return {
        'hash': parts[0],
        'short': parts[1],
        'message': parts[2],
        'author': parts[3],
        'email': parts[4],
        'date': parts[5],
        'branch': get_current_branch(),
    }


def calculate_journey_totals(session: dict) -> dict:
    """Calculate summary totals from the session attempts."""
    attempts = session.get('attempts', [])
    if not attempts:
        return {}

    started_at = session.get('started_at')
    completed_at = session.get('completed_at')

    total_duration = 0.0
    if started_at and completed_at:
        with suppress(ValueError):
            start = datetime.fromisoformat(started_at)
            end = datetime.fromisoformat(completed_at)
            total_duration = (end - start).total_seconds()

    total_errors_fixed: dict[str, int] = {}
    hooks_that_blocked: list[str] = []

    for attempt in attempts:
        hooks = attempt.get('hooks', {})
        for hook_name, hook_data in hooks.items():
            if not isinstance(hook_data, dict):
                continue

            issues = hook_data.get('issues_before_fix', 0) + hook_data.get('errors', 0) + hook_data.get('issues', 0)
            if issues > 0:
                total_errors_fixed[hook_name] = total_errors_fixed.get(hook_name, 0) + issues

            if hook_data.get('status') == 'failed' and hook_name not in hooks_that_blocked:
                hooks_that_blocked.append(hook_name)

    return {
        'started_at': started_at,
        'completed_at': completed_at,
        'total_duration_seconds': round(total_duration, 2),
        'total_attempts': len(attempts),
        'total_errors_fixed': total_errors_fixed,
        'hooks_that_blocked': hooks_that_blocked,
    }


def finalize_session(stats: dict) -> Path | None:
    """Finalize the commit session after successful commit.

    Returns the path to the saved session file, or None if no session.
    """
    session_file = get_session_file()

    if not session_file.exists():
        print('No session file found - commit may have used --no-verify')
        return None

    try:
        session = json.loads(session_file.read_text())
    except json.JSONDecodeError:
        print(f'Warning: Could not parse session file: {session_file}')
        return None

    session['status'] = 'completed'
    session['completed_at'] = datetime.now(UTC).isoformat()

    session['commit'] = get_commit_info()

    # Batch enrich file history (uses batch radon calls - much faster)
    staged_files = session.get('staged_files', [])
    filepaths = [f.get('path', '') for f in staged_files if f.get('path')]
    print(f'Enriching file history for {len(filepaths)} files...')

    enriched = enrich_files(filepaths)

    files_with_history = {}
    for file_info in staged_files:
        filepath = file_info.get('path', '')
        if filepath and filepath in enriched:
            files_with_history[filepath] = {
                **file_info,
                'git_history': enriched[filepath],
            }
    session['files'] = files_with_history

    session['journey'] = calculate_journey_totals(session)

    session['final_stats'] = stats

    SESSIONS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    commit_short = session['commit'].get('short', 'unknown')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = SESSIONS_OUTPUT_DIR / f'session_{timestamp}_{commit_short}.json'
    output_path.write_text(json.dumps(session, indent=2))

    session_file.unlink()
    print(f'Session finalized and saved to: {output_path}')

    return output_path


def main() -> int:
    """Collect stats for the current commit and sync to S3."""
    print('\n' + '=' * 60)
    print('COLLECTING PROJECT STATS (post-commit)')
    print('=' * 60 + '\n')

    pytest_json_path = '/tmp/ichrisbirch-pytest-report.json'
    stats = collect_all_stats(pytest_json_path if Path(pytest_json_path).exists() else None)

    display_stats(stats)

    filepath = save_stats(stats)
    print(f'\nStats saved to: {filepath}')

    session_path = finalize_session(stats)
    if session_path:
        print(f'Session journey saved to: {session_path}')

    print('\nSyncing stats to S3...')
    if push_stats():
        print('Stats synced to S3 successfully')
    else:
        print('Warning: Failed to sync stats to S3 (will retry on next commit)')

    return 0


if __name__ == '__main__':
    sys.exit(main())
