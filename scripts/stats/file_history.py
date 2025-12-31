#!/usr/bin/env python
"""Extract git history and file metrics.

Used by post-commit to enrich session data with file lifecycle information,
including filesystem metadata, line counts, complexity metrics, and more.
"""

from __future__ import annotations

import json
import subprocess
from contextlib import suppress
from datetime import UTC
from datetime import datetime
from pathlib import Path


def run_git(*args: str) -> str:
    """Run a git command and return stdout."""
    result = subprocess.run(
        ['git', *args],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def get_file_filesystem_info(filepath: str) -> dict:
    """Get filesystem metadata for a file.

    Returns modification time and size.
    Note: We don't track creation time (st_birthtime) because git operations
    (checkout, pull, merge, history rewrites) reset it, making it meaningless.
    """
    path = Path(filepath)
    if not path.exists():
        return {
            'exists': False,
            'size_bytes': 0,
            'modified_at': None,
        }

    stat = path.stat()
    modified_at = datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat()

    return {
        'exists': True,
        'size_bytes': stat.st_size,
        'modified_at': modified_at,
    }


def get_file_line_stats(filepath: str) -> dict:
    """Get line count statistics for a file."""
    path = Path(filepath)
    if not path.exists():
        return {'total_lines': 0, 'code_lines': 0, 'blank_lines': 0, 'comment_lines': 0}

    try:
        content = path.read_text(errors='ignore')
    except Exception:
        return {'total_lines': 0, 'code_lines': 0, 'blank_lines': 0, 'comment_lines': 0}

    lines = content.split('\n')
    if lines and lines[-1] == '':
        lines = lines[:-1]
    total = len(lines)
    blank = sum(1 for line in lines if not line.strip())

    comment = 0
    is_python = filepath.endswith('.py')
    is_shell = filepath.endswith(('.sh', '.bash'))
    is_yaml = filepath.endswith(('.yml', '.yaml'))

    in_multiline_string = False
    for line in lines:
        stripped = line.strip()
        if is_python:
            if '"""' in stripped or "'''" in stripped:  # noqa: FURB108
                if 1 in (stripped.count('"""'), stripped.count("'''")):
                    in_multiline_string = not in_multiline_string
                comment += 1
            elif in_multiline_string or stripped.startswith('#'):
                comment += 1
        elif (is_shell or is_yaml) and stripped.startswith('#'):
            comment += 1

    code = total - blank - comment

    return {
        'total_lines': total,
        'code_lines': max(0, code),
        'blank_lines': blank,
        'comment_lines': comment,
    }


def get_file_complexity(filepath: str) -> dict:
    """Get complexity metrics using radon (if available).

    Returns cyclomatic complexity, maintainability index, etc.
    """
    if not filepath.endswith('.py'):
        return {'supported': False, 'reason': 'not a Python file'}

    path = Path(filepath)
    if not path.exists():
        return {'supported': False, 'reason': 'file not found'}

    result = subprocess.run(
        ['uv', 'run', 'radon', 'cc', '-j', filepath],
        capture_output=True,
        text=True,
    )

    cc_data: dict = {}
    if result.returncode == 0 and result.stdout:
        try:
            data = json.loads(result.stdout)
            if filepath in data:
                functions = data[filepath]
                if functions:
                    complexities = [f.get('complexity', 0) for f in functions]
                    cc_data = {
                        'function_count': len(functions),
                        'total_complexity': sum(complexities),
                        'avg_complexity': round(sum(complexities) / len(complexities), 2) if complexities else 0,
                        'max_complexity': max(complexities) if complexities else 0,
                        'functions': [
                            {
                                'name': f.get('name'),
                                'complexity': f.get('complexity'),
                                'rank': f.get('rank'),
                            }
                            for f in functions[:5]
                        ],
                    }
        except json.JSONDecodeError:
            pass

    mi_result = subprocess.run(
        ['uv', 'run', 'radon', 'mi', '-j', filepath],
        capture_output=True,
        text=True,
    )

    mi_data: dict = {}
    if mi_result.returncode == 0 and mi_result.stdout:
        try:
            data = json.loads(mi_result.stdout)
            if filepath in data:
                mi_info = data[filepath]
                mi_data = {
                    'maintainability_index': round(mi_info.get('mi', 0), 2),
                    'maintainability_rank': mi_info.get('rank', 'N/A'),
                }
        except json.JSONDecodeError:
            pass

    if not cc_data and not mi_data:
        return {'supported': True, 'available': False, 'reason': 'no complexity data'}

    return {'supported': True, 'available': True} | cc_data | mi_data


def get_file_first_commit(filepath: str) -> dict | None:
    """Get the first commit that introduced this file.

    Returns dict with hash, date, author or None if file has no history.
    """
    output = run_git('log', '--follow', '--diff-filter=A', '--format=%H|%aI|%an', '--', filepath)

    if not output:
        return None

    lines = output.strip().split('\n')
    if not lines or not lines[-1]:
        return None

    parts = lines[-1].split('|')
    if len(parts) < 3:
        return None

    return {
        'hash': parts[0],
        'date': parts[1],
        'author': parts[2],
    }


def get_file_last_commit_before(filepath: str, before_ref: str = 'HEAD~1') -> dict | None:
    """Get the last commit that modified this file before a given ref.

    Useful for seeing when a file was last touched before the current commit.
    """
    output = run_git('log', '-1', '--format=%H|%aI|%an', before_ref, '--', filepath)

    if not output:
        return None

    parts = output.split('|')
    if len(parts) < 3:
        return None

    return {
        'hash': parts[0],
        'date': parts[1],
        'author': parts[2],
    }


def get_file_commit_count(filepath: str) -> int:
    """Get total number of commits touching this file."""
    output = run_git('rev-list', '--count', 'HEAD', '--', filepath)
    try:
        return int(output)
    except ValueError:
        return 0


def get_file_authors(filepath: str) -> list[str]:
    """Get all unique authors who have modified this file."""
    output = run_git('log', '--format=%an', '--', filepath)
    if not output:
        return []

    authors = set(output.split('\n'))
    return sorted(authors)


def get_file_age_days(filepath: str) -> int:
    """Calculate file age in days from first commit to now."""
    first = get_file_first_commit(filepath)
    if not first:
        return 0

    try:
        first_date = datetime.fromisoformat(first['date'].replace('Z', '+00:00'))
        now = datetime.now(first_date.tzinfo)
        return (now - first_date).days
    except (ValueError, TypeError):
        return 0


def get_file_churn(filepath: str, since: str = '30 days ago') -> dict:
    """Get file churn stats (additions/deletions) over a time period."""
    output = run_git('log', f'--since={since}', '--numstat', '--format=', '--', filepath)

    total_added = 0
    total_removed = 0
    commit_count = 0

    for line in output.split('\n'):
        if not line.strip():
            continue
        parts = line.split('\t')
        if len(parts) >= 2:
            try:
                added = int(parts[0]) if parts[0] != '-' else 0
                removed = int(parts[1]) if parts[1] != '-' else 0
                total_added += added
                total_removed += removed
                commit_count += 1
            except ValueError:
                continue

    return {
        'commits': commit_count,
        'lines_added': total_added,
        'lines_removed': total_removed,
        'net_change': total_added - total_removed,
    }


def enrich_file_history(filepath: str) -> dict:
    """Get complete history and metrics for a file.

    Returns a dict with:
    - Git history (first commit, authors, age, churn)
    - Filesystem info (creation time, size)
    - Line statistics (total, code, comments, blank)
    - Complexity metrics (cyclomatic complexity, maintainability)
    """
    first_commit = get_file_first_commit(filepath)
    last_before = get_file_last_commit_before(filepath)
    fs_info = get_file_filesystem_info(filepath)
    line_stats = get_file_line_stats(filepath)
    complexity = get_file_complexity(filepath)

    first_commit_date = first_commit['date'] if first_commit else None
    total_commits = get_file_commit_count(filepath)
    is_new_file = total_commits == 0

    time_uncommitted_seconds = None
    if is_new_file and fs_info.get('modified_at'):
        with suppress(ValueError):
            modified = datetime.fromisoformat(fs_info['modified_at'])
            now = datetime.now(UTC)
            time_uncommitted_seconds = round((now - modified).total_seconds())

    return {
        'git': {
            'first_commit_date': first_commit_date,
            'first_commit_hash': first_commit['hash'][:7] if first_commit else None,
            'first_author': first_commit['author'] if first_commit else None,
            'total_commits': total_commits,
            'last_modified_before_this': last_before['date'] if last_before else None,
            'authors': get_file_authors(filepath),
            'age_days': get_file_age_days(filepath),
            'churn_30d': get_file_churn(filepath, '30 days ago'),  # noqa: FURB120
            'churn_60d': get_file_churn(filepath, '60 days ago'),
            'churn_90d': get_file_churn(filepath, '90 days ago'),
            'churn_365d': get_file_churn(filepath, '365 days ago'),
            'is_new_file': is_new_file,
        },
        'filesystem': {
            'exists': fs_info.get('exists', False),
            'size_bytes': fs_info.get('size_bytes', 0),
            'modified_at': fs_info.get('modified_at'),
            'time_uncommitted_seconds': time_uncommitted_seconds,
        },
        'lines': line_stats,
        'complexity': complexity,
    }


def enrich_files(filepaths: list[str]) -> dict[str, dict]:
    """Enrich multiple files with history data.

    Returns a dict mapping filepath to history data.
    """
    return {fp: enrich_file_history(fp) for fp in filepaths}


if __name__ == '__main__':
    import json
    import sys

    if len(sys.argv) < 2:
        print('Usage: file_history.py <filepath> [filepath2 ...]')
        sys.exit(1)

    for filepath in sys.argv[1:]:
        if not Path(filepath).exists():
            print(f'Warning: {filepath} does not exist (may be deleted)')

        history = enrich_file_history(filepath)
        print(f'\n{filepath}:')
        print(json.dumps(history, indent=2))
