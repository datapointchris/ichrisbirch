"""Tests for the shared API exception shapes.

The not-found detail is read by someone who is stuck: `icb` prints it verbatim
and the Vue app surfaces it. So the noun in it is held to being a word a caller
can look up, rather than the internal spelling of a table or a route.
"""

import ast
from typing import Any

import pytest

from ichrisbirch.api.exceptions import NotFoundException
from ichrisbirch.util import find_project_root

SOURCE_ROOT = find_project_root() / 'ichrisbirch'


def not_found_nouns() -> list[tuple[str, int, str]]:
    """Every literal resource_type passed to NotFoundException, with where it is raised.

    Parsed rather than imported so a raise site behind a branch still counts.
    A computed noun (a variable, an f-string) yields no literal and is skipped:
    this checks the spellings written into the source, which is all of them today.
    """
    found = []
    for path in sorted(SOURCE_ROOT.rglob('*.py')):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, 'attr', '')
            if name != 'NotFoundException':
                continue
            if isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                found.append((str(path.relative_to(SOURCE_ROOT)), node.lineno, node.args[0].value))
    return found


class RecordingLogger:
    """Takes the structlog keyword call NotFoundException makes, and remembers it."""

    def __init__(self) -> None:
        self.warnings: list[tuple[str, dict[str, Any]]] = []

    def warning(self, event: str, **kwargs: Any) -> None:
        self.warnings.append((event, kwargs))


class TestNotFoundException:
    def test_detail_is_the_noun_then_the_id_then_not_found(self):
        exception = NotFoundException('project item', 999999, RecordingLogger())
        assert exception.detail == 'project item 999999 not found'

    def test_every_raise_site_is_parsed(self):
        """Guards the sweep below: an ast walk that matches nothing passes vacuously."""
        assert len(not_found_nouns()) > 20

    @pytest.mark.parametrize('source, line, noun', not_found_nouns())
    def test_the_noun_is_words_not_an_internal_spelling(self, source, line, noun):
        head, _, _ = noun.partition(' with ')
        assert '_' not in head, (
            f'{source}:{line} raises a not-found naming {noun!r}. '
            f'The caller reads this and cannot type an underscored noun — write it as words.'
        )
