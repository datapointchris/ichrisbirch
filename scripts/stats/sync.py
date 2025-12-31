#!/usr/bin/env python
"""Sync stats directory with S3 bucket.

Usage:
    # Push local stats to S3
    python -m scripts.stats.sync push

    # Pull stats from S3 to local
    python -m scripts.stats.sync pull

    # Sync both directions (pull then push)
    python -m scripts.stats.sync
"""

import argparse
import subprocess
import sys
from pathlib import Path

STATS_DIR = Path(__file__).parent.parent.parent / 'stats'
SESSIONS_DIR = STATS_DIR / 'sessions'
S3_STATS_BUCKET = 's3://ichrisbirch-stats/project-stats/'
S3_SESSIONS_BUCKET = 's3://ichrisbirch-stats/sessions/'


def run_aws_command(cmd: list[str]) -> tuple[int, str, str]:
    """Run an AWS CLI command and return exit code, stdout, stderr."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def push_stats() -> bool:
    """Push local stats and sessions to S3."""
    success = True

    if STATS_DIR.exists():
        stats_files = list(STATS_DIR.glob('stats_*.json'))
        if stats_files:
            print(f'Pushing {len(stats_files)} stats files to S3...')
            cmd = ['aws', 's3', 'sync', str(STATS_DIR), S3_STATS_BUCKET, '--exclude', '*', '--include', 'stats_*.json']
            code, stdout, stderr = run_aws_command(cmd)
            if code != 0:
                print(f'Failed to push stats: {stderr}')
                success = False
            elif stdout:
                print(stdout)

    if SESSIONS_DIR.exists():
        session_files = list(SESSIONS_DIR.glob('session_*.json'))
        if session_files:
            print(f'Pushing {len(session_files)} session files to S3...')
            cmd = ['aws', 's3', 'sync', str(SESSIONS_DIR), S3_SESSIONS_BUCKET]
            code, stdout, stderr = run_aws_command(cmd)
            if code != 0:
                print(f'Failed to push sessions: {stderr}')
                success = False
            elif stdout:
                print(stdout)

    if success:
        print('Stats and sessions pushed successfully')
    return success


def pull_stats() -> bool:
    """Pull stats and sessions from S3 to local."""
    success = True

    STATS_DIR.mkdir(exist_ok=True)
    print('Pulling stats from S3...')
    cmd = ['aws', 's3', 'sync', S3_STATS_BUCKET, str(STATS_DIR), '--exclude', '*', '--include', 'stats_*.json']
    code, stdout, stderr = run_aws_command(cmd)
    if code != 0:
        print(f'Failed to pull stats: {stderr}')
        success = False
    elif stdout:
        print(stdout)

    SESSIONS_DIR.mkdir(exist_ok=True)
    print('Pulling sessions from S3...')
    cmd = ['aws', 's3', 'sync', S3_SESSIONS_BUCKET, str(SESSIONS_DIR)]
    code, stdout, stderr = run_aws_command(cmd)
    if code != 0:
        print(f'Failed to pull sessions: {stderr}')
        success = False
    elif stdout:
        print(stdout)

    if success:
        print('Stats and sessions pulled successfully')
    return success


def main():
    parser = argparse.ArgumentParser(description='Sync stats with S3')
    parser.add_argument('action', nargs='?', choices=['push', 'pull'], default=None, help='push or pull')
    args = parser.parse_args()

    if args.action == 'push':
        success = push_stats()
    elif args.action == 'pull':
        success = pull_stats()
    else:
        # Default: pull then push (full sync)
        print('Syncing stats (pull then push)...')
        success = pull_stats() and push_stats()

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
