"""`project_items.number` moving from an identity to the shared sequence, run through alembic.

The switch runs once against a table that has issued numbers for years. An item
numbered by hand above the identity shows only in the highest surviving number.
A deleted item above every survivor shows only in the identity's own counter.
Each is a case, and the sequence must start above both.
"""

from collections.abc import Callable

import pytest
import sqlalchemy as sa
from alembic import command

from ichrisbirch.database.initialization import alembic_config
from ichrisbirch.database.session import get_db_engine
from tests.utils.database import test_settings

BEFORE_ISSUES = 'b7c8d9e0f1a2'
PROBE = 'sequence probe'


@pytest.fixture
def engine():
    engine = get_db_engine(test_settings)
    yield engine
    command.upgrade(alembic_config(test_settings), 'head')
    with engine.begin() as conn:
        conn.execute(sa.text('DELETE FROM project_items WHERE title = :title'), {'title': PROBE})
        conn.execute(sa.text('DELETE FROM issues WHERE title = :title'), {'title': PROBE})


def insert_item(conn, number: int | None = None) -> int:
    columns = 'id, title, completed, archived' + (', number' if number is not None else '')
    values = 'gen_random_uuid(), :title, false, false' + (', :number' if number is not None else '')
    statement = sa.text(f'INSERT INTO project_items ({columns}) VALUES ({values}) RETURNING number')
    return conn.execute(statement, {'title': PROBE, 'number': number}).scalar_one()


def insert_issue(conn) -> int:
    statement = sa.text('INSERT INTO issues (id, title, rank) VALUES (gen_random_uuid(), :title, 1) RETURNING number')
    return conn.execute(statement, {'title': PROBE}).scalar_one()


def an_item_numbered_by_hand_above_the_identity(conn, issued: list[int]) -> None:
    issued.append(insert_item(conn, number=max(issued) + 10))


def the_highest_item_deleted(conn, issued: list[int]) -> None:
    conn.execute(sa.text('DELETE FROM project_items WHERE number = :number'), {'number': max(issued)})


@pytest.mark.parametrize('history', [an_item_numbered_by_hand_above_the_identity, the_highest_item_deleted])
def test_no_number_is_issued_twice_across_the_switch(engine, history: Callable[..., None]):
    # The deleted issue's number stays drawn from the sequence. The downgrade
    # across the move into issues refuses while any issue exists.
    with engine.begin() as conn:
        issued = [insert_issue(conn)]
        conn.execute(sa.text('DELETE FROM issues WHERE title = :title'), {'title': PROBE})

    command.downgrade(alembic_config(test_settings), BEFORE_ISSUES)
    with engine.begin() as conn:
        issued += [insert_item(conn) for _ in range(3)]
        history(conn, issued)

    command.upgrade(alembic_config(test_settings), 'head')
    with engine.begin() as conn:
        issue_number, item_number = insert_issue(conn), insert_item(conn)

    assert issued[1] > issued[0], 'the downgrade restarted the identity at or below a number an issue held'
    assert min(issue_number, item_number) > max(issued)
    assert issue_number != item_number
