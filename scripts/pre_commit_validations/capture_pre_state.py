#!/usr/bin/env python
"""Capture pre-commit state BEFORE any fixes are applied.

This must be the FIRST hook in pre-commit config to capture:
- Staged files and their stats
- Linting issues that will be auto-fixed
- All errors/warnings before any modifications

The captured data is stored in .tmp/commit-session.json and accumulated
across multiple commit attempts until a successful commit.
"""

from __future__ import annotations

import json
import subprocess
import sys
import uuid
from datetime import UTC
from datetime import datetime
from pathlib import Path

SESSION_DIR = Path('.tmp')
HOOK_OUTPUT_DIR = Path('.tmp/hook-outputs')


def get_session_file() -> Path:
    """Get session file path for current branch."""
    branch = get_current_branch()
    safe_branch = branch.replace('/', '-').replace('\\', '-')
    return SESSION_DIR / f'session-{safe_branch}.json'


def get_staged_files() -> list[dict]:
    """Get list of staged files with diff stats."""
    result = subprocess.run(
        ['git', 'diff', '--cached', '--numstat'],
        capture_output=True,
        text=True,
    )

    status_result = subprocess.run(
        ['git', 'diff', '--cached', '--name-status'],
        capture_output=True,
        text=True,
    )

    status_map = {}
    for line in status_result.stdout.strip().split('\n'):
        if line:
            parts = line.split('\t')
            if len(parts) >= 2:
                status_code = parts[0][0]
                filepath = parts[-1]
                status_map[filepath] = {
                    'M': 'modified',
                    'A': 'added',
                    'D': 'deleted',
                    'R': 'renamed',
                    'C': 'copied',
                }.get(status_code, 'unknown')

    files = []
    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) >= 3:
            added = int(parts[0]) if parts[0] != '-' else 0
            removed = int(parts[1]) if parts[1] != '-' else 0
            filepath = parts[2]
            files.append(
                {
                    'path': filepath,
                    'status': status_map.get(filepath, 'modified'),
                    'lines_added': added,
                    'lines_removed': removed,
                }
            )

    return files


def capture_ruff_issues(staged_files: list[dict]) -> dict:
    """Run ruff in check-only mode (no --fix) to capture issues."""
    python_files = [f['path'] for f in staged_files if f['path'].endswith('.py')]

    if not python_files:
        return {'status': 'skipped', 'reason': 'no python files', 'issues_before_fix': 0}

    result = subprocess.run(
        ['uv', 'run', 'ruff', 'check', '--output-format', 'json', *python_files],
        capture_output=True,
        text=True,
    )

    output_file = HOOK_OUTPUT_DIR / 'ruff-output.json'
    output_file.write_text(result.stdout or '[]')

    try:
        issues = json.loads(result.stdout) if result.stdout else []
    except json.JSONDecodeError:
        issues = []

    issues_by_type: dict[str, int] = {}
    files_affected: set[str] = set()
    for issue in issues:
        code = issue.get('code', 'unknown')
        issues_by_type[code] = issues_by_type.get(code, 0) + 1
        if filename := issue.get('filename'):
            files_affected.add(filename)

    status = 'would_fix' if issues else 'passed'

    return {
        'status': status,
        'issues_before_fix': len(issues),
        'issues_by_type': issues_by_type,
        'files_affected': list(files_affected),
        'output_snippet': result.stdout[:500] if result.stdout else '',
    }


def capture_mypy_issues(staged_files: list[dict]) -> dict:
    """Run mypy and capture all errors."""
    python_files = [f['path'] for f in staged_files if f['path'].endswith('.py')]

    if not python_files:
        return {'status': 'skipped', 'reason': 'no python files', 'errors': 0}

    result = subprocess.run(
        ['uv', 'run', 'mypy', '--config-file', 'pyproject.toml', *python_files],
        capture_output=True,
        text=True,
    )

    output_file = HOOK_OUTPUT_DIR / 'mypy-output.txt'
    output_file.write_text(result.stdout + result.stderr)

    error_count = 0
    files_affected: set[str] = set()
    for line in result.stdout.split('\n'):
        if ': error:' in line:
            error_count += 1
            filepath = line.split(':')[0]
            files_affected.add(filepath)

    status = 'failed' if result.returncode != 0 else 'passed'

    return {
        'status': status,
        'errors': error_count,
        'files_affected': list(files_affected),
        'output_snippet': (result.stdout + result.stderr)[:500],
    }


def capture_shellcheck_issues(staged_files: list[dict]) -> dict:
    """Run shellcheck on shell scripts."""
    shell_files = [f['path'] for f in staged_files if f['path'].endswith(('.sh', '.bash')) or 'cli/' in f['path']]

    if not shell_files:
        return {'status': 'skipped', 'reason': 'no shell files', 'issues': 0}

    existing_files = [f for f in shell_files if Path(f).exists()]
    if not existing_files:
        return {'status': 'skipped', 'reason': 'no existing shell files', 'issues': 0}

    result = subprocess.run(
        ['shellcheck', '--format', 'json', *existing_files],
        capture_output=True,
        text=True,
    )

    output_file = HOOK_OUTPUT_DIR / 'shellcheck-output.json'
    output_file.write_text(result.stdout or '[]')

    try:
        issues = json.loads(result.stdout) if result.stdout else []
    except json.JSONDecodeError:
        issues = []

    issues_by_severity: dict[str, int] = {'error': 0, 'warning': 0, 'info': 0, 'style': 0}
    files_affected: set[str] = set()
    for issue in issues:
        level = issue.get('level', 'warning')
        issues_by_severity[level] = issues_by_severity.get(level, 0) + 1
        if filename := issue.get('file'):
            files_affected.add(filename)

    status = 'warning' if issues else 'passed'

    return {
        'status': status,
        'issues': len(issues),
        'issues_by_severity': issues_by_severity,
        'files_affected': list(files_affected),
        'output_snippet': result.stdout[:500] if result.stdout else '',
    }


def capture_bandit_issues(staged_files: list[dict]) -> dict:
    """Run bandit security scanner."""
    python_files = [f['path'] for f in staged_files if f['path'].endswith('.py')]

    if not python_files:
        return {'status': 'skipped', 'reason': 'no python files', 'issues': 0}

    existing_files = [f for f in python_files if Path(f).exists()]
    if not existing_files:
        return {'status': 'skipped', 'reason': 'no existing python files', 'issues': 0}

    result = subprocess.run(
        ['uv', 'run', 'bandit', '-c', 'pyproject.toml', '-f', 'json', *existing_files],
        capture_output=True,
        text=True,
    )

    output_file = HOOK_OUTPUT_DIR / 'bandit-output.json'
    output_file.write_text(result.stdout or '{}')

    try:
        report = json.loads(result.stdout) if result.stdout else {}
    except json.JSONDecodeError:
        report = {}

    issues = report.get('results', [])
    issues_by_severity: dict[str, int] = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
    files_affected: set[str] = set()
    for issue in issues:
        severity = issue.get('issue_severity', 'LOW')
        issues_by_severity[severity] = issues_by_severity.get(severity, 0) + 1
        if filename := issue.get('filename'):
            files_affected.add(filename)

    status = 'failed' if issues else 'passed'

    return {
        'status': status,
        'issues': len(issues),
        'issues_by_severity': issues_by_severity,
        'files_affected': list(files_affected),
        'output_snippet': result.stdout[:500] if result.stdout else '',
    }


def capture_codespell_issues(staged_files: list[dict]) -> dict:
    """Run codespell to check for spelling errors."""
    files = [f['path'] for f in staged_files if Path(f['path']).exists()]

    if not files:
        return {'status': 'skipped', 'reason': 'no files', 'issues': 0}

    result = subprocess.run(
        ['codespell', '--toml', 'pyproject.toml', *files],
        capture_output=True,
        text=True,
    )

    output_file = HOOK_OUTPUT_DIR / 'codespell-output.txt'
    output_file.write_text(result.stdout + result.stderr)

    issue_count = len([line for line in result.stdout.split('\n') if line.strip()])
    status = 'failed' if result.returncode != 0 else 'passed'

    return {
        'status': status,
        'issues': issue_count,
        'output_snippet': result.stdout[:500] if result.stdout else '',
    }


def get_current_branch() -> str:
    """Get the current git branch name."""
    result = subprocess.run(
        ['git', 'branch', '--show-current'],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def load_or_create_session(staged_files: list[dict]) -> dict:
    """Load existing session for current branch or create a new one."""
    session_file = get_session_file()
    if session_file.exists():
        try:
            return json.loads(session_file.read_text())
        except json.JSONDecodeError:
            pass

    return create_new_session(staged_files)


def create_new_session(staged_files: list[dict]) -> dict:
    """Create a new commit session."""
    return {
        'session_id': str(uuid.uuid4()),
        'branch': get_current_branch(),
        'started_at': datetime.now(UTC).isoformat(),
        'last_updated': datetime.now(UTC).isoformat(),
        'status': 'active',
        'staged_files': staged_files,
        'attempts': [],
    }


def add_attempt(session: dict, hooks: dict, start_time: datetime) -> None:
    """Add a new attempt to the session."""
    attempt_number = len(session['attempts']) + 1
    duration = (datetime.now(UTC) - start_time).total_seconds()

    attempt = {
        'attempt_number': attempt_number,
        'timestamp': start_time.isoformat(),
        'duration_seconds': round(duration, 2),
        'result': 'in_progress',
        'hooks': hooks,
    }

    session['attempts'].append(attempt)
    session['last_updated'] = datetime.now(UTC).isoformat()


def main() -> int:
    """Main entry point - captures all pre-state and updates session."""
    HOOK_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    start_time = datetime.now(UTC)
    staged_files = get_staged_files()

    if not staged_files:
        print('No staged files to capture')
        return 0

    print(f'Capturing pre-commit state for {len(staged_files)} staged files...')

    hooks = {
        'ruff': capture_ruff_issues(staged_files),
        'mypy': capture_mypy_issues(staged_files),
        'shellcheck': capture_shellcheck_issues(staged_files),
        'bandit': capture_bandit_issues(staged_files),
        'codespell': capture_codespell_issues(staged_files),
    }

    session = load_or_create_session(staged_files)
    session['staged_files'] = staged_files
    add_attempt(session, hooks, start_time)

    session_file = get_session_file()
    session_file.parent.mkdir(parents=True, exist_ok=True)
    session_file.write_text(json.dumps(session, indent=2))

    total_issues = sum(
        h.get('issues_before_fix', 0) + h.get('errors', 0) + h.get('issues', 0) for h in hooks.values() if isinstance(h, dict)
    )

    print(f'Pre-state captured: {total_issues} issues found across {len(staged_files)} files')
    print(f'Attempt #{len(session["attempts"])} logged to {session_file}')

    return 0


if __name__ == '__main__':
    sys.exit(main())
