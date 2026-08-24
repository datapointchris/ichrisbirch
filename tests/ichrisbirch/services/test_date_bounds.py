"""A bound has to match the type of the column it narrows.

`apply_date_bounds` promises both ends inclusive. Comparing a `Date` column against
an aware `datetime` breaks that promise without erroring: Postgres casts the bound
in the session `TimeZone`, so `2026-08-20` resolves to the 19th on any session west
of UTC and every book finished on the 20th drops out of its own range.
"""

import datetime as dt

import pytest
import sqlalchemy as sa

from ichrisbirch import models
from ichrisbirch.services.date_bounds import apply_date_bounds


def _bound_values(column, start: str | None = None, end: str | None = None):
    """The literal on the right of each comparison the bounds added.

    One bound produces a BinaryExpression and two produce a BooleanClauseList, so
    both shapes are flattened rather than assuming the two-bound case.
    """
    where = apply_date_bounds(sa.select(models.Book), column, start, end).whereclause
    if where is None:
        return []
    clauses = getattr(where, 'clauses', [where])
    return [clause.right.value for clause in clauses]


def test_a_date_column_gets_a_date_bound():
    values = _bound_values(models.Book.read_finish_date, start='2026-08-20', end='2026-08-25')
    assert values == [dt.date(2026, 8, 20), dt.date(2026, 8, 25)]
    assert all(not isinstance(v, dt.datetime) for v in values)


def test_a_timestamp_column_keeps_its_datetime_bound():
    values = _bound_values(models.Task.complete_date, start='2026-08-20')
    assert isinstance(values[0], dt.datetime)


def test_a_bound_carrying_a_time_still_narrows_a_date_column():
    """A caller may send a full datetime; the day is what a date column compares."""
    values = _bound_values(models.Book.read_finish_date, start='2026-08-20T18:45:00Z')
    assert values == [dt.date(2026, 8, 20)]


@pytest.mark.parametrize('session_zone', ['UTC', 'America/Chicago', 'Pacific/Auckland'])
def test_the_inclusive_end_keeps_its_own_day_whatever_the_session_zone(factory_session, session_zone):
    conn = factory_session.connection()
    conn.execute(sa.text(f"SET LOCAL TimeZone = '{session_zone}'"))

    same_day = conn.execute(sa.text("SELECT DATE '2026-08-20' <= DATE '2026-08-20'")).scalar_one()
    assert same_day, 'a date compared against a date has no zone in it'
