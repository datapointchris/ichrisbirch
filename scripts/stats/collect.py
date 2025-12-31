#!/usr/bin/env python
"""Collect project stats and save to JSON.

This script collects comprehensive project metrics including:
- Git commit information
- Code statistics (tokei)
- Test results and coverage (from pre-commit output or fresh run)
- Docker image information
- Dependency counts
- Quality metrics (ruff, mypy, bandit issues)

Usage:
    # Collect and display stats (no save)
    python -m scripts.stats.collect

    # Collect for a specific commit (saves to stats/)
    python -m scripts.stats.collect --commit

    # Use pre-commit pytest output
    python -m scripts.stats.collect --commit --pytest-json /tmp/ichrisbirch-pytest-report.json
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

STATS_DIR = Path(__file__).parent.parent.parent / 'stats'
ICHRISBIRCH_DIR = Path(__file__).parent.parent.parent / 'ichrisbirch'
PROJECT_ROOT = Path(__file__).parent.parent.parent


def run_command(cmd: list[str], capture_json: bool = False) -> dict | str | None:
    """Run a command and return output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            logger.warning(f'Command {cmd[0]} failed: {result.stderr}')
            return None
        output = result.stdout.strip()
        if capture_json and output:
            return json.loads(output)
        return output
    except subprocess.TimeoutExpired:
        logger.error(f'Command {cmd[0]} timed out')
        return None
    except json.JSONDecodeError as e:
        logger.warning(f'Failed to parse JSON from {cmd[0]}: {e}')
        return None
    except FileNotFoundError:
        logger.warning(f'Command not found: {cmd[0]}')
        return None


def get_git_info() -> dict[str, Any]:
    """Get current git commit information."""
    git_hash = run_command(['git', 'rev-parse', 'HEAD'])
    short_hash = run_command(['git', 'rev-parse', '--short', 'HEAD'])
    author = run_command(['git', 'log', '-1', '--format=%an'])
    email = run_command(['git', 'log', '-1', '--format=%ae'])
    date = run_command(['git', 'log', '-1', '--format=%aI'])
    message = run_command(['git', 'log', '-1', '--format=%s'])
    branch = run_command(['git', 'branch', '--show-current'])

    # Get diff stats for this commit
    diff_stat = run_command(['git', 'diff', '--shortstat', 'HEAD~1', 'HEAD'])
    files_changed = 0
    insertions = 0
    deletions = 0
    if diff_stat and isinstance(diff_stat, str):
        parts = diff_stat.split(',')
        for part in parts:
            part = part.strip()
            if 'file' in part:
                files_changed = int(part.split()[0])
            elif 'insertion' in part:
                insertions = int(part.split()[0])
            elif 'deletion' in part:
                deletions = int(part.split()[0])

    return {
        'hash': git_hash or 'unknown',
        'short': short_hash or 'unknown',
        'author': author or 'unknown',
        'email': email or 'unknown',
        'date': date or datetime.now(UTC).isoformat(),
        'message': message or '',
        'branch': branch or 'unknown',
        'files_changed': files_changed,
        'insertions': insertions,
        'deletions': deletions,
    }


def get_tokei_stats() -> dict[str, Any]:
    """Get code statistics from tokei."""
    tokei_output = run_command(['tokei', str(ICHRISBIRCH_DIR), '--output', 'json'], capture_json=True)
    if not tokei_output or not isinstance(tokei_output, dict):
        return {}

    # Summarize by language
    summary = {}
    total_code = 0
    total_comments = 0
    total_blanks = 0

    for lang, data in tokei_output.items():
        if isinstance(data, dict) and 'code' in data:
            summary[lang] = {
                'code': data.get('code', 0),
                'comments': data.get('comments', 0),
                'blanks': data.get('blanks', 0),
                'files': len(data.get('reports', [])),
            }
            total_code += data.get('code', 0)
            total_comments += data.get('comments', 0)
            total_blanks += data.get('blanks', 0)

    return {
        'languages': summary,
        'total': {
            'code': total_code,
            'comments': total_comments,
            'blanks': total_blanks,
        },
    }


def get_test_stats(pytest_json_path: str | None = None) -> dict[str, Any]:
    """Get test statistics from pytest JSON report."""
    report = None

    # Try to read from provided path first
    if pytest_json_path and Path(pytest_json_path).exists():
        try:
            report = json.loads(Path(pytest_json_path).read_text())
            logger.info(f'Loaded pytest report from {pytest_json_path}')
        except json.JSONDecodeError:
            logger.warning(f'Failed to parse pytest JSON from {pytest_json_path}')

    # If no report, try the default temp location
    if not report:
        default_path = Path('/tmp/ichrisbirch-pytest-report.json')
        if default_path.exists():
            try:
                report = json.loads(default_path.read_text())
                logger.info(f'Loaded pytest report from {default_path}')
            except json.JSONDecodeError:
                pass

    if not report:
        # No cached report - just get test count without running
        result = subprocess.run(
            ['uv', 'run', 'pytest', '--collect-only', '-q'],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            env=os.environ | {'ENVIRONMENT': 'testing'},
        )
        # Parse "X tests collected" from output
        test_count = 0
        for line in result.stdout.split('\n'):
            if 'test' in line and 'collected' in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part in ('tests', 'test'):
                        test_count = int(parts[i - 1])
                        break
        return {
            'total': test_count,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0,
            'duration_seconds': 0,
            'slowest': [],
            'source': 'collect-only',
        }

    # Parse the pytest-json-report format
    summary = report.get('summary', {})
    tests = report.get('tests', [])

    # Get slowest tests
    slowest = []
    if tests:
        sorted_tests = sorted(tests, key=lambda t: t.get('duration', 0), reverse=True)
        for test in sorted_tests[:10]:
            slowest.append(
                {
                    'name': test.get('nodeid', 'unknown'),
                    'duration': round(test.get('duration', 0), 3),
                    'outcome': test.get('outcome', 'unknown'),
                }
            )

    return {
        'total': summary.get('total', 0),
        'passed': summary.get('passed', 0),
        'failed': summary.get('failed', 0),
        'skipped': summary.get('skipped', 0),
        'errors': summary.get('error', 0),
        'duration_seconds': round(report.get('duration', 0), 2),
        'slowest': slowest,
        'source': 'pytest-json-report',
    }


def get_coverage_stats(pytest_json_path: str | None = None) -> dict[str, Any]:
    """Get coverage statistics."""
    # Try to find coverage data from pytest run
    coverage_json = Path(PROJECT_ROOT) / '.coverage.json'

    # Try running coverage json if no cached data
    if not coverage_json.exists():
        result = subprocess.run(
            ['uv', 'run', 'coverage', 'json', '-o', str(coverage_json)],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        if result.returncode != 0:
            return {'line_percent': 0, 'missing_lines': 0, 'source': 'unavailable'}

    if coverage_json.exists():
        try:
            data = json.loads(coverage_json.read_text())
            totals = data.get('totals', {})
            return {
                'line_percent': round(totals.get('percent_covered', 0), 2),
                'covered_lines': totals.get('covered_lines', 0),
                'missing_lines': totals.get('missing_lines', 0),
                'excluded_lines': totals.get('excluded_lines', 0),
                'num_statements': totals.get('num_statements', 0),
                'source': 'coverage.py',
            }
        except json.JSONDecodeError:
            pass

    return {'line_percent': 0, 'missing_lines': 0, 'source': 'unavailable'}


def get_docker_stats() -> dict[str, Any]:
    """Get Docker image statistics."""
    # Get ichrisbirch images
    result = subprocess.run(
        ['docker', 'images', '--format', '{{json .}}'],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return {'images': [], 'total_size_mb': 0}

    images = []
    total_size = 0.0

    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        try:
            img = json.loads(line)
            repo = img.get('Repository', '')
            if 'ichrisbirch' in repo.lower():
                size_str = img.get('Size', '0B')
                # Parse size (e.g., "3.25GB", "395MB")
                size_mb = 0.0
                if 'GB' in size_str:
                    size_mb = float(size_str.replace('GB', '')) * 1024
                elif 'MB' in size_str:
                    size_mb = float(size_str.replace('MB', ''))
                elif 'KB' in size_str:
                    size_mb = float(size_str.replace('KB', '')) / 1024

                images.append(
                    {
                        'repository': repo,
                        'tag': img.get('Tag', 'latest'),
                        'size_mb': round(size_mb, 1),
                        'created': img.get('CreatedAt', ''),
                        'id': img.get('ID', '')[:12],
                    }
                )
                total_size += size_mb
        except json.JSONDecodeError:
            continue

    return {
        'images': images,
        'total_size_mb': round(total_size, 1),
        'count': len(images),
    }


def get_dependency_stats() -> dict[str, Any]:
    """Get dependency statistics from uv.lock or pyproject.toml."""
    # Count dependencies from pyproject.toml
    pyproject = PROJECT_ROOT / 'pyproject.toml'
    if not pyproject.exists():
        return {'direct': 0, 'total': 0}

    content = pyproject.read_text()
    direct_deps = 0
    dev_deps = 0

    in_deps = False
    in_dev_deps = False
    for line in content.split('\n'):
        if line.strip() == '[project.dependencies]' or line.strip().startswith('dependencies = ['):
            in_deps = True
            continue
        if line.strip() == '[tool.uv.dev-dependencies]' or line.strip().startswith('dev-dependencies = ['):
            in_dev_deps = True
            continue
        if line.strip().startswith('[') and not line.strip().startswith(('dependencies', 'dev-dependencies')):
            in_deps = False
            in_dev_deps = False
            continue
        if in_deps and line.strip() and not line.strip().startswith('#') and line.strip() != ']' and ('"' in line or "'" in line):
            direct_deps += 1
        if in_dev_deps and line.strip() and not line.strip().startswith('#') and line.strip() != ']' and ('"' in line or "'" in line):
            dev_deps += 1

    # Count total from uv.lock
    uv_lock = PROJECT_ROOT / 'uv.lock'
    total_deps = 0
    if uv_lock.exists():
        lock_content = uv_lock.read_text()
        total_deps = lock_content.count('[[package]]')

    return {
        'direct': direct_deps,
        'dev': dev_deps,
        'total': total_deps,
    }


def get_quality_stats() -> dict[str, Any]:
    """Get code quality statistics from pre-commit hook outputs.

    These tools already ran in pre-commit, so we read from cached outputs
    instead of re-running them (saves ~15 seconds).
    """
    quality = {
        'ruff_issues': 0,
        'mypy_errors': 0,
        'bandit_issues': 0,
    }

    # Read from pre-commit hook outputs if available
    hook_output_dir = PROJECT_ROOT / '.tmp' / 'hook-outputs'

    # Ruff output
    ruff_output = hook_output_dir / 'ruff-output.json'
    if ruff_output.exists():
        try:
            issues = json.loads(ruff_output.read_text())
            quality['ruff_issues'] = len(issues) if isinstance(issues, list) else 0
        except json.JSONDecodeError:
            pass

    # Mypy output
    mypy_output = hook_output_dir / 'mypy-output.txt'
    if mypy_output.exists():
        content = mypy_output.read_text()
        quality['mypy_errors'] = content.count(': error:')

    # Bandit output
    bandit_output = hook_output_dir / 'bandit-output.json'
    if bandit_output.exists():
        try:
            bandit_data = json.loads(bandit_output.read_text())
            quality['bandit_issues'] = len(bandit_data.get('results', []))
        except json.JSONDecodeError:
            pass

    return quality


def collect_all_stats(pytest_json_path: str | None = None) -> dict[str, Any]:
    """Collect all project statistics."""
    logger.info('Collecting git info...')
    git_info = get_git_info()

    logger.info('Collecting tokei stats...')
    tokei_stats = get_tokei_stats()

    logger.info('Collecting test stats...')
    test_stats = get_test_stats(pytest_json_path)

    logger.info('Collecting coverage stats...')
    coverage_stats = get_coverage_stats(pytest_json_path)

    logger.info('Collecting Docker stats...')
    docker_stats = get_docker_stats()

    logger.info('Collecting dependency stats...')
    dep_stats = get_dependency_stats()

    logger.info('Collecting quality stats...')
    quality_stats = get_quality_stats()

    return {
        'collected_at': datetime.now(UTC).isoformat(),
        'commit': git_info,
        'code': tokei_stats,
        'tests': test_stats,
        'coverage': coverage_stats,
        'docker': docker_stats,
        'dependencies': dep_stats,
        'quality': quality_stats,
    }


def save_stats(stats: dict[str, Any]) -> Path:
    """Save stats to JSON file in stats directory."""
    STATS_DIR.mkdir(exist_ok=True)

    commit_short = stats['commit']['short']
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = STATS_DIR / f'stats_{timestamp}_{commit_short}.json'

    filename.write_text(json.dumps(stats, indent=2))
    logger.info(f'Stats saved to {filename}')
    return filename


def display_stats(stats: dict[str, Any]) -> None:
    """Display stats in a readable format."""
    print('\n' + '=' * 60)
    print('PROJECT STATS')
    print('=' * 60)

    # Git
    commit = stats['commit']
    print(f'\nCommit: {commit["short"]} ({commit["branch"]})')
    print(f'Author: {commit["author"]}')
    print(f'Message: {commit["message"][:60]}...')
    print(f'Changes: {commit["files_changed"]} files, +{commit["insertions"]}/-{commit["deletions"]}')

    # Code
    code = stats.get('code', {})
    total = code.get('total', {})
    print(f'\nCode: {total.get("code", 0):,} lines')
    print(f'Comments: {total.get("comments", 0):,} lines')
    print(f'Languages: {", ".join(code.get("languages", {}).keys())}')

    # Tests
    tests = stats.get('tests', {})
    print(f'\nTests: {tests.get("total", 0)} total')
    print(f'Passed: {tests.get("passed", 0)}, Failed: {tests.get("failed", 0)}, Skipped: {tests.get("skipped", 0)}')
    print(f'Duration: {tests.get("duration_seconds", 0):.1f}s')

    # Coverage
    cov = stats.get('coverage', {})
    print(f'\nCoverage: {cov.get("line_percent", 0):.1f}%')

    # Docker
    docker = stats.get('docker', {})
    print(f'\nDocker Images: {docker.get("count", 0)}')
    print(f'Total Size: {docker.get("total_size_mb", 0):.1f} MB')

    # Dependencies
    deps = stats.get('dependencies', {})
    print(f'\nDependencies: {deps.get("direct", 0)} direct, {deps.get("total", 0)} total')

    # Quality
    quality = stats.get('quality', {})
    print('\nQuality Issues:')
    print(f'  Ruff: {quality.get("ruff_issues", 0)}')
    print(f'  Mypy: {quality.get("mypy_errors", 0)}')
    print(f'  Bandit: {quality.get("bandit_issues", 0)}')

    print('\n' + '=' * 60)


def main():
    parser = argparse.ArgumentParser(description='Collect project statistics')
    parser.add_argument('--commit', action='store_true', help='Save stats for current commit')
    parser.add_argument('--pytest-json', type=str, help='Path to pytest JSON report')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(levelname)s: %(message)s',
    )

    stats = collect_all_stats(args.pytest_json)
    display_stats(stats)

    if args.commit:
        filepath = save_stats(stats)
        print(f'\nStats saved to: {filepath}')
    else:
        print('\nRun with --commit to save stats for this commit')

    return 0


if __name__ == '__main__':
    sys.exit(main())
