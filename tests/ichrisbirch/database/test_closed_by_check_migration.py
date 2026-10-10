"""The CHECK keeping `closed_by` null on an open issue, run through alembic."""

import datetime as dt
from uuid import UUID
from uuid import uuid7

import pytest
import sqlalchemy as sa
from alembic import command

from ichrisbirch.database.initialization import alembic_config
from ichrisbirch.database.session import get_db_engine
from tests.utils.database import test_settings

BEFORE_CHECK = '816ce25c08dc'
CLOSED_AT = dt.datetime(2026, 10, 10, 12, 0, tzinfo=dt.UTC)
CLOSER = 'claude-code/probe'


def add_issue(conn, title: str, status: str) -> UUID:
    issue_id = uuid7()
    conn.execute(
        sa.text(
            'INSERT INTO issues (id, title, status, rank, closed_ts, closed_by) VALUES (:id, :title, :status, 0, :closed_ts, :closed_by)'
        ),
        {'id': issue_id, 'title': title, 'status': status, 'closed_ts': CLOSED_AT if status == 'completed' else None, 'closed_by': CLOSER},
    )
    return issue_id


@pytest.fixture
def issues():
    engine = get_db_engine(test_settings)
    config = alembic_config(test_settings)
    ids: dict[str, UUID] = {}
    command.downgrade(config, BEFORE_CHECK)
    try:
        with engine.begin() as conn:
            ids['reopened'] = add_issue(conn, 'closed_by probe reopened', 'open')
            ids['completed'] = add_issue(conn, 'closed_by probe completed', 'completed')
        command.upgrade(config, 'head')
        yield engine, ids
    finally:
        command.upgrade(config, 'head')
        with engine.begin() as conn:
            conn.execute(sa.text('DELETE FROM issues WHERE id = ANY(:ids)'), {'ids': list(ids.values())})


def closer(engine, issue_id: UUID) -> str | None:
    with engine.connect() as conn:
        return conn.execute(sa.text('SELECT closed_by FROM issues WHERE id = :id'), {'id': issue_id}).scalar_one()


def test_a_closer_left_on_a_reopened_issue_is_cleared_before_the_check_is_added(issues):
    """The outgoing color reopens an issue and leaves `closed_by`. Postgres checks
    every row as the constraint is added, so one such row fails the deploy."""
    engine, ids = issues

    assert closer(engine, ids['reopened']) is None
    assert closer(engine, ids['completed']) == CLOSER


def test_an_open_issue_can_no_longer_carry_a_closer(issues):
    engine, ids = issues

    with pytest.raises(sa.exc.IntegrityError, match='issue_closed_by_only_when_closed'), engine.begin() as conn:
        conn.execute(sa.text('UPDATE issues SET closed_by = :closer WHERE id = :id'), {'closer': CLOSER, 'id': ids['reopened']})
