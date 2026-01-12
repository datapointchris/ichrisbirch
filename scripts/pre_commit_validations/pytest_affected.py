"""Run pytest for staged Python files only.

This pre-commit hook maps staged source files to their corresponding test files
and runs them with fail-fast mode for quick feedback.

Directory mapping: ichrisbirch/app/login.py → tests/ichrisbirch/app/test_login.py
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


def get_staged_python_files() -> list[Path]:
    """Get list of staged Python files (Added, Copied, Modified)."""
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM', '--', '*.py'],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []

    return [Path(f) for f in result.stdout.strip().split('\n') if f]


def map_source_to_test(source_file: Path, project_root: Path) -> Path | None:
    """Map a source file to its corresponding test file.

    Args:
        source_file: Path like ichrisbirch/app/login.py
        project_root: Project root directory

    Returns:
        Test file path like tests/ichrisbirch/app/test_login.py, or None if not found
    """
    source_str = str(source_file)

    # Skip conftest.py files - they're fixtures, not tests
    # Changes to conftest.py affect all tests, handled by full test suite
    if source_file.name == 'conftest.py':
        return None

    # If this is already a test file, return it directly
    # But skip utility modules (conftest, environment, utils, test_data, etc.)
    if source_str.startswith('tests/') and source_file.suffix == '.py':
        # Skip known utility directories and files
        utility_patterns = ['utils', 'test_data', 'environment.py', '__init__.py']
        if any(pattern in source_str for pattern in utility_patterns):
            return None
        test_path = project_root / source_file
        return test_path if test_path.exists() else None

    # Map ichrisbirch/ source files to tests/ichrisbirch/
    if source_str.startswith('ichrisbirch/'):
        # ichrisbirch/app/login.py → app/login.py
        rel_path = Path(source_str.removeprefix('ichrisbirch/'))
        parent = rel_path.parent
        stem = rel_path.stem

        # tests/ichrisbirch/app/test_login.py
        test_path = project_root / 'tests' / 'ichrisbirch' / parent / f'test_{stem}.py'
        return test_path if test_path.exists() else None

    return None


def main() -> int:
    """Main entry point for the pre-commit hook."""
    project_root = get_project_root()
    os.chdir(project_root)
    os.environ['ENVIRONMENT'] = 'testing'

    staged_files = get_staged_python_files()

    if not staged_files:
        print('No staged Python files - skipping affected tests')
        return 0

    print('Staged Python files:')
    for f in staged_files:
        print(f'  {f}')
    print(flush=True)

    # Map to test files
    test_files: set[Path] = set()

    for source_file in staged_files:
        test_file = map_source_to_test(source_file, project_root)
        if test_file:
            test_files.add(test_file)
            print(f'  Mapped: {source_file} → {test_file.relative_to(project_root)}')
        else:
            print(f'  No test found for: {source_file}')

    print(flush=True)

    if not test_files:
        print('No corresponding test files found for staged changes')
        return 0

    print('Running affected tests...')
    print(flush=True)

    test_paths = [str(t.relative_to(project_root)) for t in sorted(test_files)]
    result = subprocess.run(
        ['uv', 'run', 'pytest', '--tb=short', *test_paths],
    )

    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
