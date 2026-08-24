"""The `timestamptz` → `date` conversion, run against a row that has a value.

Every other check runs `upgrade()` on a fresh database, so the six `AT TIME ZONE
'UTC'` clauses alter empty tables and are never evaluated. Deleting them entirely
leaves the suite green, which makes those checks evidence of nothing.

These build the pre-migration shape in a temporary table, run the same expressions
the migration runs, and assert the day survives — under a session zone west of UTC,
which is where relying on the session `TimeZone` would lose a day.
"""

import datetime as dt

import pytest
import sqlalchemy as sa

UPGRADE = "(value AT TIME ZONE 'UTC')::date"
DOWNGRADE = "value::timestamp AT TIME ZONE 'UTC'"


@pytest.fixture
def conn(factory_session):
    return factory_session.connection()


def _stored_day(conn, session_zone: str, stored: str) -> dt.date:
    conn.execute(sa.text(f"SET LOCAL TimeZone = '{session_zone}'"))
    conn.execute(sa.text('CREATE TEMP TABLE probe (value timestamptz) ON COMMIT DROP'))
    conn.execute(sa.text('INSERT INTO probe VALUES (:v)'), {'v': stored})
    conn.execute(sa.text(f'ALTER TABLE probe ALTER COLUMN value TYPE date USING {UPGRADE}'))
    return conn.execute(sa.text('SELECT value FROM probe')).scalar_one()


@pytest.mark.parametrize('session_zone', ['UTC', 'America/Chicago', 'Pacific/Auckland'])
def test_the_typed_day_survives_whatever_the_session_zone_is(conn, session_zone):
    assert _stored_day(conn, session_zone, '2026-08-20 00:00:00+00') == dt.date(2026, 8, 20)


def test_without_the_pinned_zone_a_western_session_loses_a_day(conn):
    """The clause is load-bearing, so its absence has to look different."""
    conn.execute(sa.text("SET LOCAL TimeZone = 'America/Chicago'"))
    conn.execute(sa.text('CREATE TEMP TABLE probe (value timestamptz) ON COMMIT DROP'))
    conn.execute(sa.text('INSERT INTO probe VALUES (:v)'), {'v': '2026-08-20 00:00:00+00'})

    unpinned = conn.execute(sa.text('SELECT value::date FROM probe')).scalar_one()
    pinned = conn.execute(sa.text(f'SELECT {UPGRADE} FROM probe')).scalar_one()

    assert unpinned == dt.date(2026, 8, 19)
    assert pinned == dt.date(2026, 8, 20)


def test_the_downgrade_returns_the_instant_the_column_held(conn):
    conn.execute(sa.text("SET LOCAL TimeZone = 'America/Chicago'"))
    conn.execute(sa.text('CREATE TEMP TABLE probe (value date) ON COMMIT DROP'))
    conn.execute(sa.text('INSERT INTO probe VALUES (:v)'), {'v': '2026-08-20'})
    conn.execute(sa.text(f'ALTER TABLE probe ALTER COLUMN value TYPE timestamptz USING {DOWNGRADE}'))

    restored = conn.execute(sa.text('SELECT value FROM probe')).scalar_one()

    assert restored == dt.datetime(2026, 8, 20, 0, 0, tzinfo=dt.UTC)
