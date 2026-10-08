"""Development work moving from projects into issues, run through alembic."""

import datetime as dt
from dataclasses import dataclass
from dataclasses import field
from uuid import UUID
from uuid import uuid7

import pytest
import sqlalchemy as sa
from alembic import command

from ichrisbirch.database.initialization import alembic_config
from ichrisbirch.database.session import get_db_engine
from tests.utils.database import test_settings

BEFORE_MOVE = 'c8d9e0f1a2b3'
FINISHED_AT = dt.datetime(2026, 9, 1, 12, 0, tzinfo=dt.UTC)


@dataclass
class Before:
    projects: dict[str, UUID] = field(default_factory=dict)
    items: dict[str, UUID] = field(default_factory=dict)
    numbers: dict[str, int] = field(default_factory=dict)


def add_project(conn, before: Before, key: str, kind: str, status: str, position: int, reason: str | None = None) -> None:
    before.projects[key] = uuid7()
    conn.execute(
        sa.text(
            'INSERT INTO projects (id, name, kind, status, status_reason, closed_at, position) '
            'VALUES (:id, :name, :kind, :status, :reason, :closed_at, :position)'
        ),
        {
            'id': before.projects[key],
            'name': f'move probe {key}',
            'kind': kind,
            'status': status,
            'reason': reason,
            'closed_at': FINISHED_AT if status in ('completed', 'dropped') else None,
            'position': position,
        },
    )


def add_item(
    conn,
    before: Before,
    key: str,
    memberships: dict[str, int],
    *,
    completed: bool = False,
    archived: bool = False,
    notes: str | None = None,
) -> None:
    before.items[key] = uuid7()
    before.numbers[key] = conn.execute(
        sa.text(
            'INSERT INTO project_items (id, title, notes, completed, completed_at, archived) '
            'VALUES (:id, :title, :notes, :completed, :completed_at, :archived) RETURNING number'
        ),
        {
            'id': before.items[key],
            'title': f'move probe {key}',
            'notes': notes,
            'completed': completed,
            'completed_at': FINISHED_AT if completed else None,
            'archived': archived,
        },
    ).scalar_one()
    for project, position in memberships.items():
        conn.execute(
            sa.text('INSERT INTO project_item_memberships (item_id, project_id, position) VALUES (:item, :project, :position)'),
            {'item': before.items[key], 'project': before.projects[project], 'position': position},
        )


def add_task(conn, before: Before, item: str, title: str, position: int, *, completed: bool) -> None:
    conn.execute(
        sa.text(
            'INSERT INTO project_item_tasks (id, item_id, title, completed, position) VALUES (:id, :item, :title, :completed, :position)'
        ),
        {'id': uuid7(), 'item': before.items[item], 'title': title, 'completed': completed, 'position': position},
    )


def add_edge(conn, before: Before, item: str, depends_on: str) -> None:
    conn.execute(
        sa.text('INSERT INTO project_item_dependencies (item_id, depends_on_id) VALUES (:item, :depends_on)'),
        {'item': before.items[item], 'depends_on': before.items[depends_on]},
    )


def write_before(conn, before: Before) -> None:
    add_project(conn, before, 'build-first', 'build', 'active', 0)
    add_project(conn, before, 'build-second', 'build', 'active', 1)
    add_project(conn, before, 'build-third', 'build', 'active', 2)
    add_project(conn, before, 'build-fourth', 'build', 'active', 3)
    add_project(conn, before, 'build-completed', 'build', 'completed', 4)
    add_project(conn, before, 'build-dropped', 'build', 'dropped', 5, reason='gave up')
    add_project(conn, before, 'build-someday', 'build', 'someday', 6)
    add_project(conn, before, 'life', 'life', 'active', 7)

    add_item(conn, before, 'open-with-tasks', {'build-first': 1}, notes='what the agent needs')
    add_item(conn, before, 'finished-then-archived', {'build-first': 0}, completed=True, archived=True)
    add_item(conn, before, 'archived-unfinished', {'build-second': 0}, archived=True)
    add_item(conn, before, 'in-two-active', {'build-fourth': 0, 'build-second': 5})
    add_item(conn, before, 'in-active-and-completed', {'build-completed': 0, 'build-first': 9})
    add_item(conn, before, 'in-completed-only', {'build-completed': 1})
    add_item(conn, before, 'build-and-life', {'build-first': 2, 'life': 0})
    add_item(conn, before, 'life-only', {'life': 1}, notes='a personal note')

    add_task(conn, before, 'open-with-tasks', 'second', 1, completed=False)
    add_task(conn, before, 'open-with-tasks', 'first', 0, completed=True)

    add_edge(conn, before, 'open-with-tasks', 'archived-unfinished')
    add_edge(conn, before, 'in-two-active', 'life-only')
    add_edge(conn, before, 'life-only', 'in-completed-only')


@pytest.fixture(scope='module')
def moved():
    engine = get_db_engine(test_settings)
    config = alembic_config(test_settings)
    before = Before()
    command.downgrade(config, BEFORE_MOVE)
    try:
        with engine.begin() as conn:
            write_before(conn, before)
        command.upgrade(config, 'head')
        yield engine, before
    finally:
        command.upgrade(config, 'head')
        with engine.begin() as conn:
            conn.execute(sa.text('DELETE FROM issues WHERE id = ANY(:ids)'), {'ids': list(before.items.values())})
            conn.execute(sa.text('DELETE FROM initiatives WHERE id = ANY(:ids)'), {'ids': list(before.projects.values())})
            conn.execute(sa.text('DELETE FROM project_items WHERE id = ANY(:ids)'), {'ids': list(before.items.values())})
            conn.execute(sa.text('DELETE FROM projects WHERE id = ANY(:ids)'), {'ids': list(before.projects.values())})


def issue_rows(engine, before: Before) -> dict[str, sa.Row]:
    keys = {item_id: key for key, item_id in before.items.items()}
    with engine.connect() as conn:
        rows = conn.execute(sa.text('SELECT * FROM issues WHERE id = ANY(:ids)'), {'ids': list(keys)}).all()
    return {keys[row.id]: row for row in rows}


def test_build_projects_become_initiatives_ranked_in_thirds(moved):
    engine, before = moved
    with engine.connect() as conn:
        rows = conn.execute(
            sa.text('SELECT id, status, status_reason, priority FROM initiatives WHERE id = ANY(:ids)'),
            {'ids': list(before.projects.values())},
        ).all()
    keys = {project_id: key for key, project_id in before.projects.items()}
    initiatives = {keys[row.id]: (row.status, row.status_reason, row.priority) for row in rows}

    assert initiatives == {
        'build-first': ('active', None, 2),
        'build-second': ('active', None, 2),
        'build-third': ('active', None, 3),
        'build-fourth': ('active', None, 4),
        'build-completed': ('completed', None, 0),
        'build-dropped': ('dropped', 'gave up', 0),
        'build-someday': ('active', None, 0),
    }


def test_items_keep_their_id_and_number(moved):
    engine, before = moved
    issues = issue_rows(engine, before)

    moved_keys = set(before.items) - {'build-and-life', 'life-only'}
    assert set(issues) == moved_keys
    assert {key: issues[key].number for key in moved_keys} == {key: before.numbers[key] for key in moved_keys}


def test_completed_wins_over_archived_and_archived_alone_is_canceled(moved):
    engine, before = moved
    issues = issue_rows(engine, before)

    assert (issues['finished-then-archived'].status, issues['finished-then-archived'].closed_ts) == ('completed', FINISHED_AT)
    assert (issues['archived-unfinished'].status, issues['archived-unfinished'].status_reason) == (
        'canceled',
        'Archived as a project item',
    )
    assert (issues['open-with-tasks'].status, issues['open-with-tasks'].closed_ts) == ('open', None)


def test_notes_and_sub_tasks_become_description_and_checklist(moved):
    engine, before = moved
    issue = issue_rows(engine, before)['open-with-tasks']

    assert issue.description == 'what the agent needs'
    assert issue.acceptance == '- [x] first\n- [ ] second'


def test_an_item_joins_its_active_project_with_the_lowest_position(moved):
    engine, before = moved
    issues = issue_rows(engine, before)

    assert issues['in-two-active'].initiative_id == before.projects['build-second']
    assert issues['in-active-and-completed'].initiative_id == before.projects['build-first']
    assert issues['in-completed-only'].initiative_id == before.projects['build-completed']


def test_rank_follows_project_order_then_position_in_the_project(moved):
    engine, before = moved
    issues = issue_rows(engine, before)

    assert sorted(issues, key=lambda key: issues[key].rank) == [
        'finished-then-archived',
        'open-with-tasks',
        'in-active-and-completed',
        'archived-unfinished',
        'in-two-active',
        'in-completed-only',
    ]


def test_an_edge_between_moved_items_is_copied(moved):
    engine, before = moved
    moved_ids = list(before.items.values())
    with engine.connect() as conn:
        edges = conn.execute(
            sa.text('SELECT issue_id, depends_on_id FROM issue_dependencies WHERE issue_id = ANY(:ids)'), {'ids': moved_ids}
        ).all()

    assert [tuple(edge) for edge in edges] == [(before.items['open-with-tasks'], before.items['archived-unfinished'])]


def test_an_edge_crossing_the_stores_becomes_a_line_on_the_dependent(moved):
    engine, before = moved
    issues = issue_rows(engine, before)
    with engine.connect() as conn:
        staying_notes = conn.execute(
            sa.text('SELECT notes FROM project_items WHERE id = :id'), {'id': before.items['life-only']}
        ).scalar_one()

    assert issues['in-two-active'].description == f'Depends on project item {before.numbers["life-only"]}.'
    assert staying_notes == f'a personal note\n\nDepends on issue {before.numbers["in-completed-only"]}.'


def test_only_life_projects_and_their_items_remain(moved):
    engine, before = moved
    with engine.connect() as conn:
        projects = conn.execute(sa.text('SELECT id FROM projects WHERE id = ANY(:ids)'), {'ids': list(before.projects.values())}).scalars()
        items = conn.execute(sa.text('SELECT id FROM project_items WHERE id = ANY(:ids)'), {'ids': list(before.items.values())}).scalars()
        memberships = conn.execute(
            sa.text('SELECT project_id FROM project_item_memberships WHERE item_id = :id'), {'id': before.items['build-and-life']}
        ).scalars()

        assert set(projects) == {before.projects['life']}
        assert set(items) == {before.items['build-and-life'], before.items['life-only']}
        assert list(memberships) == [before.projects['life']]


def test_the_downgrade_refuses_while_issues_hold_rows(moved):
    with pytest.raises(NotImplementedError, match='restore from backup'):
        command.downgrade(alembic_config(test_settings), BEFORE_MOVE)
