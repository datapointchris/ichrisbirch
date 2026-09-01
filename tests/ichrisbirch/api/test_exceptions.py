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


def not_found_raises() -> list[tuple[str, int, str | None]]:
    """Every NotFoundException raise site, with its resource_type when that is a literal.

    Parsed rather than imported so a raise site behind a branch still counts.
    A site whose noun is computed — a variable, an f-string — yields None, and
    the test below fails on it rather than skipping it. A skip would let a
    single indirection take a raise site out of the sweep with nothing said.
    """
    found: list[tuple[str, int, str | None]] = []
    for path in sorted(SOURCE_ROOT.rglob('*.py')):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, 'attr', '')
            if name != 'NotFoundException':
                continue
            noun = node.args[0].value if isinstance(node.args[0], ast.Constant) else None
            found.append((str(path.relative_to(SOURCE_ROOT)), node.lineno, noun if isinstance(noun, str) else None))
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

    def test_the_walk_finds_every_raise_site_the_source_holds(self):
        """Guards the sweep: an ast walk that stops matching passes vacuously.

        Counted against the source text itself rather than a number written
        here, so adding a raise site does not fail this and moving one out of
        the walk's reach does.
        """
        walked = len(not_found_raises())
        written = sum(
            path.read_text().count('NotFoundException(') for path in SOURCE_ROOT.rglob('*.py') if 'exceptions.py' not in path.name
        )
        assert walked == written, f'the walk found {walked} raise sites and the source holds {written}'

    @pytest.mark.parametrize('source, line, noun', not_found_raises())
    def test_the_noun_is_words_not_an_internal_spelling(self, source, line, noun):
        assert noun is not None, (
            f'{source}:{line} raises a not-found whose resource_type is not a literal, '
            f'so nothing here can check how it is spelled. Pass the noun inline.'
        )
        head, _, _ = noun.partition(' with ')
        assert '_' not in head, (
            f'{source}:{line} raises a not-found naming {noun!r}. '
            f'The caller reads this and cannot type an underscored noun — write it as words.'
        )
