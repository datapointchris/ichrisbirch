"""Utility functions for documentation tools.

This module provides shared utilities for documentation generation tools,
avoiding the need for sys.path manipulation or fragile relative imports.
"""

from pathlib import Path


def find_project_root(start_path: Path | None = None, marker: str = 'pyproject.toml') -> Path:
    """Find the project root directory by looking for a marker file.

    Args:
        start_path: Starting directory for search. Defaults to this file's directory.
        marker: File name that indicates project root. Defaults to 'pyproject.toml'.

    Returns:
        Path to project root directory.

    Raises:
        FileNotFoundError: If marker file is not found in any parent directory.
    """
    if start_path is None:
        start_path = Path(__file__).resolve().parent

    current = start_path
    while current != current.parent:
        if (current / marker).exists():
            return current
        current = current.parent

    raise FileNotFoundError(f'Could not find {marker} in any parent directory of {start_path}')
