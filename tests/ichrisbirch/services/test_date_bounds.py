"""A bound has to match the type of the column it narrows and the bound's own shape.

`apply_date_bounds` promises both ends inclusive. Comparing a `Date` column against
an aware `datetime` breaks that promise without erroring: Postgres casts the bound
in the session `TimeZone`, so `2026-08-20` resolves to the 19th on any session west
of UTC and every book finished on the 20th drops out of its own range.

A bare day closing a timestamp column breaks it the other way. The day resolves to
the instant it begins, so `<=` keeps only rows stamped exactly midnight and
`--start X --end X` answers with nothing on a column that stores a time.

Read in UTC, a bare day puts a task finished at 21:00 in New York on the next day,
so the request's zone decides where the day opens and closes. A time written with
no offset is read on the same clock.
"""

import datetime as dt
from zoneinfo import ZoneInfo

import pytest
import sqlalchemy as sa
from fastapi import HTTPException

from ichrisbirch import models
from ichrisbirch.services.date_bounds import apply_date_bounds
from ichrisbirch.services.date_bounds import day_bounds

NEW_YORK = ZoneInfo('America/New_York')


def _where(column, start: str | None = None, end: str | None = None, zone: str | None = 'UTC'):
    return apply_date_bounds(sa.select(models.Book), column, start, end, timezone=zone).whereclause


def _bound_values(column, start: str | None = None, end: str | None = None, zone: str | None = 'UTC'):
    """The literal on the right of each comparison the bounds added.

    One bound produces a BinaryExpression and two produce a BooleanClauseList, so
    both shapes are flattened rather than assuming the two-bound case.
    """
    where = _where(column, start, end, zone)
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


def test_a_time_with_no_offset_is_read_on_the_request_zones_clock():
    """20:00 typed in New York is 00:00 UTC the next day, never 20:00 UTC."""
    values = _bound_values(models.Task.complete_date, start='2026-09-20T20:00:00', zone='America/New_York')

    assert values == [dt.datetime(2026, 9, 20, 20, tzinfo=NEW_YORK)]
    assert values[0].astimezone(dt.UTC) == dt.datetime(2026, 9, 21, 0, tzinfo=dt.UTC)


def test_a_time_with_an_offset_keeps_it_whatever_the_zone():
    values = _bound_values(models.Task.complete_date, start='2026-08-20T04:00:00Z', zone='Asia/Tokyo')
    assert values == [dt.datetime(2026, 8, 20, 4, tzinfo=dt.UTC)]


def test_a_time_with_an_offset_needs_no_zone():
    values = _bound_values(models.Task.complete_date, start='2026-08-20T04:00:00Z', zone=None)
    assert values == [dt.datetime(2026, 8, 20, 4, tzinfo=dt.UTC)]


@pytest.mark.parametrize('bound', ['2026-08-20', '2026-08-20T20:00:00'])
def test_a_bound_with_no_offset_on_a_timestamp_column_without_a_zone_is_refused(bound):
    """Guessed as UTC, the 20th would run from 20:00 on the 19th to 20:00 on the 20th in New York."""
    with pytest.raises(TypeError, match='needs a zone'):
        _bound_values(models.Task.complete_date, start=bound, zone=None)


def test_a_bound_carrying_a_time_still_narrows_a_date_column():
    """A caller may send a full datetime; the day is what a date column compares."""
    values = _bound_values(models.Book.read_finish_date, start='2026-08-20T18:45:00Z')
    assert values == [dt.date(2026, 8, 20)]


def _end_clause(column, end: str, zone: str | None = 'UTC'):
    """The operator and the literal of the single comparison an end bound added."""
    where = _where(column, end=end, zone=zone)
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


def test_a_bare_day_on_a_timestamp_column_is_that_day_in_the_callers_zone():
    """21:00 in New York on the 20th is 01:00 on the 21st in UTC.

    Read as a UTC day, the 20th would leave that task out and the 21st would
    claim it.
    """
    where = _where(models.Task.complete_date, '2026-08-20', '2026-08-20', 'America/New_York')
    opens, closes = (clause.right.value for clause in where.clauses)

    evening = dt.datetime(2026, 8, 20, 21, 0, tzinfo=NEW_YORK)
    assert opens <= evening < closes
    assert evening.astimezone(dt.UTC).date() == dt.date(2026, 8, 21)


def test_a_zone_leaves_a_date_column_alone():
    """A `Date` column already holds a calendar day, so no zone can move it."""
    where = _where(models.Book.read_finish_date, start='2026-08-20', zone='Pacific/Auckland')

    assert where.right.value == dt.date(2026, 8, 20)


def test_an_end_bound_carrying_a_time_is_left_exactly_as_written():
    """An instant is an edge the caller placed, not a day to widen.

    A window ending at midnight on the 21st would take in all of the 21st if the
    end were stretched to the close of its day.
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
        _where(models.Task.complete_date, start=value)

    assert caught.value.status_code == 422


@pytest.mark.parametrize('session_zone', ['UTC', 'America/Chicago', 'Pacific/Auckland'])
def test_the_inclusive_end_keeps_its_own_day_whatever_the_session_zone(factory_session, session_zone):
    conn = factory_session.connection()
    conn.execute(sa.text(f"SET LOCAL TimeZone = '{session_zone}'"))

    same_day = conn.execute(sa.text("SELECT DATE '2026-08-20' <= DATE '2026-08-20'")).scalar_one()
    assert same_day, 'a date compared against a date has no zone in it'


class TestDayBounds:
    def test_the_window_is_half_open(self):
        """A row stamped at the stroke of midnight belongs to the day it opens."""
        opens, closes = day_bounds(dt.date(2026, 9, 20), NEW_YORK)

        assert opens == dt.datetime(2026, 9, 20, 0, 0, tzinfo=NEW_YORK)
        assert closes == dt.datetime(2026, 9, 21, 0, 0, tzinfo=NEW_YORK)

    def test_a_spring_forward_day_is_twenty_three_hours(self):
        """Built from the next calendar day, not by adding a fixed duration.

        Adding 24 hours to midnight lands at 01:00 on the day the offset moves,
        so an hour of the next day would be counted against this one.

        Measured in UTC. Subtracting two aware datetimes that share one tzinfo is
        computed as if both were naive, so `closes - opens` reads 24 hours here
        however far apart the two instants really are.
        """
        opens, closes = day_bounds(dt.date(2026, 3, 8), NEW_YORK)

        assert closes.astimezone(dt.UTC) - opens.astimezone(dt.UTC) == dt.timedelta(hours=23)
        assert closes == dt.datetime(2026, 3, 9, 0, 0, tzinfo=NEW_YORK)

    def test_a_fall_back_day_is_twenty_five_hours(self):
        opens, closes = day_bounds(dt.date(2026, 11, 1), NEW_YORK)

        assert closes.astimezone(dt.UTC) - opens.astimezone(dt.UTC) == dt.timedelta(hours=25)
