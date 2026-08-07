"""Repository walk shared by the collectors that scan the working tree.

`Path.rglob` descends into every directory and leaves the caller to discard
what it does not want, so a collector interested in 433 source files walks the
31,000 paths under `.venv` and `node_modules` first. Pruning during the walk is
what makes the post-commit collect cheap enough not to be noticed.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

SKIP_DIRS = frozenset({'.git', '.venv', 'node_modules', '__pycache__', '.pytest_cache', '.mypy_cache'})


def iter_files(root: str = '.', suffix: str | None = None) -> Iterator[Path]:
    """Yield every file under root, skipping SKIP_DIRS without descending into them.

    Args:
        root: Directory to walk
        suffix: Only yield files ending with this (e.g. '.py'); all files when None
    """
    for dirpath, dirnames, filenames in Path(root).walk():
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            if suffix is None or filename.endswith(suffix):
                yield dirpath / filename
