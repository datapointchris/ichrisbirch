"""Run a rewriting tool on copies of the staged files, so capture measures without writing.

Capture runs inside a pre-commit hook. pre-commit fails any hook that changes a
tracked file, so a fixer run on the real paths fails the commit even though
capture exists only to record what the fixer would do.
"""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def scratch_copies(paths: list[str]) -> Iterator[dict[str, str]]:
    """Copy each existing path into a temporary directory, yielding scratch path to original.

    Each copy keeps its file name in a directory of its own, so a tool that reads
    the extension treats it as it would the original, and two staged files with
    the same name do not collide.
    """
    with tempfile.TemporaryDirectory(prefix='devstats-scratch-') as scratch_dir:
        originals: dict[str, str] = {}
        for index, path in enumerate(paths):
            if not Path(path).is_file():
                continue
            copy = Path(scratch_dir) / str(index) / Path(path).name
            copy.parent.mkdir()
            shutil.copyfile(path, copy)
            originals[str(copy)] = path
        yield originals
