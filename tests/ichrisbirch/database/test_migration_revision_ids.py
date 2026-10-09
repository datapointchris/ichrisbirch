"""Every migration file under `alembic/versions` declares its own revision ID.

Alembic warns on a reused ID and keeps one of the files. When the two revise
different parents the chain still resolves to one head, so nothing else fails.
"""

import ast
from collections import Counter
from pathlib import Path

import ichrisbirch

VERSIONS = Path(ichrisbirch.__file__).parent / 'alembic' / 'versions'


def declared_revision(path: Path) -> str:
    for node in ast.parse(path.read_text()).body:
        targets: list[ast.expr]
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        else:
            continue
        if [target.id for target in targets if isinstance(target, ast.Name)] == ['revision']:
            return ast.literal_eval(value)
    raise AssertionError(f'{path.name} declares no revision')


def test_no_two_migrations_share_a_revision_id():
    revisions = Counter(declared_revision(path) for path in VERSIONS.glob('*.py'))
    assert revisions, f'no migrations found under {VERSIONS}'
    reused = [revision for revision, count in revisions.items() if count > 1]
    assert not reused, f'revision IDs declared by more than one migration: {reused}'
