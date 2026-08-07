"""Tests for the shared collector walk."""

from __future__ import annotations

import tempfile
from pathlib import Path

from stats.collectors.walk import iter_files


def make_tree(root: Path) -> None:
    (root / 'keep.py').write_text('x = 1')
    (root / 'keep.ts').write_text('const x = 1')
    (root / 'src').mkdir()
    (root / 'src' / 'nested.py').write_text('y = 2')
    for skipped in ('.venv', 'node_modules', '__pycache__'):
        (root / skipped).mkdir()
        (root / skipped / 'ignored.py').write_text('z = 3')


def test_iter_files_yields_every_file_outside_the_skip_dirs() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        make_tree(Path(tmpdir))

        found = {p.name for p in iter_files(tmpdir)}

        assert found == {'keep.py', 'keep.ts', 'nested.py'}


def test_iter_files_filters_by_suffix() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        make_tree(Path(tmpdir))

        found = {p.name for p in iter_files(tmpdir, '.py')}

        assert found == {'keep.py', 'nested.py'}


def test_iter_files_does_not_descend_into_skipped_directories() -> None:
    """The point of the walk: pruning, not filtering after the fact.

    Filtering still pays for every path under `.venv` and `node_modules`, which
    was ten seconds of the post-commit collect on this repo.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        make_tree(Path(tmpdir))
        deep = Path(tmpdir) / 'node_modules' / 'pkg' / 'dist'
        deep.mkdir(parents=True)
        (deep / 'bundle.js').write_text('// big')

        assert not any('node_modules' in p.parts for p in iter_files(tmpdir))


def test_iter_files_yields_paths_without_a_dot_prefix() -> None:
    """Collectors store these paths, so './x.py' and 'x.py' must not both appear."""
    with tempfile.TemporaryDirectory() as tmpdir:
        make_tree(Path(tmpdir))

        relative = {str(p.relative_to(tmpdir)) for p in iter_files(tmpdir, '.py')}

        assert relative == {'keep.py', 'src/nested.py'}
