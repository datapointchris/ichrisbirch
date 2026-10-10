"""Narrow staged paths to text files, as pre-commit's `types: [text]` does."""

from __future__ import annotations

import os

from identify.identify import tags_from_path


def text_files(paths: list[str]) -> list[str]:
    """The paths naming a text file, by the classifier pre-commit applies to `types: [text]`.

    A whitespace fixer handed a binary rewrites its bytes, and an image loses the
    spaces that sat before a newline byte.
    """
    return [path for path in paths if os.path.lexists(path) and 'text' in tags_from_path(path)]
