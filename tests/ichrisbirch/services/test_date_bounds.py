"""A bound has to match the type of the column it narrows and the bound's own shape.

`apply_date_bounds` promises both ends inclusive. Comparing a `Date` column against
an aware `datetime` breaks that promise without erroring: Postgres casts the bound
in the session `TimeZone`, so `2026-08-20` resolves to the 19th on any session west
of UTC and every book finished on the 20th drops out of its own range.

A bare day closing a timestamp column breaks it the other way. The day resolves to
the instant it begins, so `<=` keeps only rows stamped exactly midnight and
`--start X --end X` answers with nothing on a column that stores a time.
"""

import datetime as dt

import pytest
import sqlalchemy as sa
from fastapi import HTTPException

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


def _end_clause(column, end: str):
    """The operator and the literal of the single comparison an end bound added."""
    where = apply_date_bounds(sa.select(models.Book), column, None, end).whereclause
    assert where is not None, 'an end bound must add a comparison'
    return where.operator.__name__, where.right.value


def test_a_bare_day_closing_a_timestamp_column_widens_to_the_next_midnight():
    """Anything else drops the day it was asked for.

    The day resolves to the instant it begins, so an inclusive compare keeps
    only rows stamped exactly midnight. The whole day is everything strictly
    before the next one.
    """
    operator, value = _end_clause(models.Task.complete_date, '2026-08-20')

    assert operator == 'lt'
    assert value == dt.datetime(2026, 8, 21, tzinfo=dt.UTC)


def test_an_end_bound_carrying_a_time_is_left_exactly_as_written():
    """The Vue habit views already send `end_date` as a full `toISOString()`.

    `habits.ts` builds tomorrow's midnight for "today", `weekEnd` for the week
    and the first of next month for the month. Widening any of those by a day
    would make each window include the one after it.
    """
    operator, value = _end_clause(models.Task.complete_date, '2026-08-21T00:00:00Z')

    assert operator == 'le'
    assert value == dt.datetime(2026, 8, 21, tzinfo=dt.UTC)


def test_a_bare_day_closing_a_date_column_stays_inclusive():
    """A `Date` column stores no time, so the day itself is already the bound."""
    operator, value = _end_clause(models.Book.read_finish_date, '2026-08-20')

    assert operator == 'le'
    assert value == dt.date(2026, 8, 20)


@pytest.mark.parametrize('value', ['nonsense', 'P1D', '17:33', ''])
def test_a_bound_that_is_not_a_date_is_a_422_rather_than_a_500(value):
    """`ParserError` is a `ValueError` and an empty string raises the bare parent.

    A bare time and a duration both parse, so neither raises at all — each has
    to be refused by type after parsing or it reaches the comparison and fails
    there as a 500 on what is the caller's mistake.
    """
    with pytest.raises(HTTPException) as caught:
        apply_date_bounds(sa.select(models.Book), models.Task.complete_date, value, None)

    assert caught.value.status_code == 422


@pytest.mark.parametrize('session_zone', ['UTC', 'America/Chicago', 'Pacific/Auckland'])
def test_the_inclusive_end_keeps_its_own_day_whatever_the_session_zone(factory_session, session_zone):
    conn = factory_session.connection()
    conn.execute(sa.text(f"SET LOCAL TimeZone = '{session_zone}'"))

    same_day = conn.execute(sa.text("SELECT DATE '2026-08-20' <= DATE '2026-08-20'")).scalar_one()
    assert same_day, 'a date compared against a date has no zone in it'
