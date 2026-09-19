"""Tests for the shared API exception shapes.

The not-found detail is read by someone who is stuck: `icb` prints it verbatim
and the Vue app surfaces it. So the noun in it is held to being a word a caller
can look up, rather than the internal spelling of a table or a route.

A failed dependency is held to 424 across the whole source. Cloudflare replaces
an origin's 502 or 504 with its own error page, so either one would reach the
caller without the detail that says what failed.
"""

import ast
from typing import Any

import pytest

from ichrisbirch.api.exceptions import FailedDependencyException
from ichrisbirch.api.exceptions import NotFoundException
from ichrisbirch.util import find_project_root

SOURCE_ROOT = find_project_root() / 'ichrisbirch'

EDGE_REPLACED_NAMES = {'HTTP_502_BAD_GATEWAY', 'HTTP_504_GATEWAY_TIMEOUT'}
EDGE_REPLACED_CODES = {502, 504}


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


def replaced_status_line(node: ast.AST) -> int | None:
    """The line where this node answers a status Cloudflare replaces, or None.

    A status reaches a response spelled two ways: as the named constant, whether
    read off `status` or imported on its own, and as the bare number passed to
    `status_code`.
    """
    if isinstance(node, ast.Attribute) and node.attr in EDGE_REPLACED_NAMES:
        return node.lineno
    if isinstance(node, ast.Name) and node.id in EDGE_REPLACED_NAMES:
        return node.lineno
    if isinstance(node, ast.keyword) and node.arg == 'status_code' and isinstance(node.value, ast.Constant):
        return node.value.lineno if node.value.value in EDGE_REPLACED_CODES else None
    return None


def edge_replaced_statuses(tree: ast.AST) -> list[int]:
    """The lines where a tree answers a status Cloudflare replaces with its own page."""
    found = (replaced_status_line(node) for node in ast.walk(tree))
    return sorted(line for line in found if line is not None)


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


class TestFailedDependencyException:
    def test_answers_424_carrying_the_detail_it_was_given(self):
        exception = FailedDependencyException({'reason': 'failed', 'message': 'failed (HTTP 401)'})
        assert exception.status_code == 424
        assert exception.detail == {'reason': 'failed', 'message': 'failed (HTTP 401)'}

    def test_the_walk_finds_every_spelling_of_a_replaced_status(self):
        """Guards the sweep below: a walk that stops matching passes it vacuously."""
        planted = ast.parse(
            'raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY)\n'
            'raise HTTPException(status_code=HTTP_504_GATEWAY_TIMEOUT)\n'
            'response = JSONResponse(status_code=502, content={})\n'
        )
        assert edge_replaced_statuses(planted) == [1, 2, 3]

    def test_no_answer_uses_a_status_cloudflare_replaces(self):
        offenders = [
            f'{path.relative_to(SOURCE_ROOT)}:{line}'
            for path in sorted(SOURCE_ROOT.rglob('*.py'))
            for line in edge_replaced_statuses(ast.parse(path.read_text(), filename=str(path)))
        ]
        assert not offenders, (
            f'{", ".join(offenders)} answer 502 or 504. Cloudflare replaces either with its own error page, '
            f'so the detail never reaches the caller. Raise FailedDependencyException instead.'
        )
