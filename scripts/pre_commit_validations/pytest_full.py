#!/usr/bin/env python
"""Run the full pytest test suite with JSON output for stats collection.

This pre-commit hook runs all tests and outputs JSON reports that can be
used by the post-commit stats collection hook.
"""

import os
import subprocess
import sys
from pathlib import Path


def get_project_root() -> Path:
    """Find project root by looking for pyproject.toml."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / 'pyproject.toml').exists():
            return current
        current = current.parent
    return Path.cwd()


def main() -> int:
    """Run full pytest suite with JSON output."""
    project_root = get_project_root()
    os.chdir(project_root)
    os.environ['ENVIRONMENT'] = 'testing'

    print('Running full test suite...')
    print(flush=True)

    # Output JSON report for stats collection
    json_report_path = '/tmp/ichrisbirch-pytest-report.json'
    result = subprocess.run(
        [
            'uv',
            'run',
            'pytest',
            '--tb=short',
            '--json-report',
            f'--json-report-file={json_report_path}',
            '--cov=ichrisbirch',
            '--cov-report=json:.coverage.json',
        ],
    )

    if result.returncode == 0:
        print(f'\nTest results saved to {json_report_path}')

    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
