"""Date-range narrowing for the list reads whose rows carry a date.

Most apps store a timestamp their collection read has no other way to narrow by,
which leaves "what did I finish this week" to be answered by fetching everything
and cutting it up client-side. `data.md` § "Filtering is server-side" puts the
`WHERE` here instead, once, so the CLI and the web client share one definition of
what a bound means.

The semantics are the ones `/habits/completed/` established: both bounds are
inclusive, each narrows on its own so one without the other is an open-ended
range, and an unparsable value is a 422 rather than a silently ignored filter.

A bound written as a bare day means the whole of that day, and one written with a
time means that instant. `--start X --end X` therefore answers with everything
dated on X, whatever the column's own type.

A bound compares against a nullable column, so a row with no date is outside
every range — an unread article is not "read before today", and an open task was
not "completed this week".
"""

import datetime as dt
from typing import Annotated

import pendulum
import sqlalchemy as sa
from fastapi import HTTPException
from fastapi import Query
from fastapi import status
from sqlalchemy import ColumnElement
from sqlalchemy import Select
from sqlalchemy.orm import InstrumentedAttribute

StartDate = Annotated[str | None, Query(description='Only rows dated on or after this ISO 8601 date')]
EndDate = Annotated[str | None, Query(description='Only rows dated on or before this ISO 8601 date')]


def _parse_bound(value: str) -> dt.datetime | dt.date:
    """The bound as the caller wrote it, keeping whether they named a time.

    `exact=True` answers a bare day with a `date` and an instant with a
    `datetime`. That distinction is the whole input to the end bound below, and
    the default parse discards it by resolving every bare day to midnight.

    `ParserError` is a `ValueError`, and an empty string raises the bare parent
    rather than the subclass, so catching the parent is what keeps `end_date=`
    a 422 instead of a 500.
    """
    try:
        parsed = pendulum.parse(value, exact=True)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f'Invalid date format: {e}') from e
    # pendulum also answers durations and bare times, which would reach the
    # comparison as a type the column cannot be compared against and surface as a
    # 500 on what is a caller's mistake.
    if not isinstance(parsed, dt.date):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f'Invalid date format: {value!r} is not a date or datetime',
        )
    return parsed


def _as_datetime(parsed: dt.datetime | dt.date) -> dt.datetime:
    """A bare day as the instant it begins, in UTC.

    UTC because the API has no other zone to reach for. A caller wanting their
    own midnight sends the instant, which is what the Vue stores already do.
    """
    if isinstance(parsed, dt.datetime):
        return parsed
    return pendulum.datetime(parsed.year, parsed.month, parsed.day)


def _as_date(parsed: dt.datetime | dt.date) -> dt.date:
    return parsed.date() if isinstance(parsed, dt.datetime) else parsed


def _is_date_column(column: InstrumentedAttribute) -> bool:
    return isinstance(column.type, sa.Date) and not isinstance(column.type, sa.DateTime)


def _criterion(column: InstrumentedAttribute, value: str, *, end: bool) -> ColumnElement[bool]:
    """One bound's comparison, matched to the column's type and the bound's own.

    A `Date` column compared against an aware `datetime` makes Postgres cast the
    bound in the session `TimeZone`, so `2026-08-20` resolves to the 19th on any
    session west of UTC and the inclusive range this module promises silently
    loses a day at each end. Comparing a date against a date has no zone in it.

    A bare day closing a timestamp column is the one case that is not `<=`. The
    day resolves to the instant it begins, so an inclusive compare would keep
    only rows stamped exactly midnight and drop the rest of the day. The whole
    day is everything strictly before the next midnight instead.

    A bound that carries a time is left exactly as written at both ends. That is
    what the gate is on, rather than on the column being a timestamp: the Vue
    habit views send `end_date` as a full `toISOString()` already, and widening
    those by a day would make "today" include tomorrow.
    """
    parsed = _parse_bound(value)
    if _is_date_column(column):
        as_written = _as_date(parsed)
        return column <= as_written if end else column >= as_written
    if end and not isinstance(parsed, dt.datetime):
        return column < _as_datetime(parsed) + dt.timedelta(days=1)
    moment = _as_datetime(parsed)
    return column <= moment if end else column >= moment


def apply_date_bounds(query: Select, column: InstrumentedAttribute, start_date: str | None, end_date: str | None) -> Select:
    """Narrow to rows whose `column` falls within the bounds, or leave it alone."""
    if start_date is not None:
        query = query.where(_criterion(column, start_date, end=False))
    if end_date is not None:
        query = query.where(_criterion(column, end_date, end=True))
    return query
