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
dated on X, whatever the column's own type. On a timestamp column the day is the
one in the request's zone, because a day is not a UTC day for anyone who does
not live in UTC: a task finished at 21:00 in New York is 01:00 the next day
there. `ichrisbirch/api/request_zone.py` decides which zone a request is in.

A bound compares against a nullable column, so a row with no date is outside
every range — an unread article is not "read before today", and an open task was
not "completed this week".
"""

import datetime as dt
from typing import Annotated
from zoneinfo import ZoneInfo

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


def day_bounds(day: dt.date, zone: ZoneInfo) -> tuple[dt.datetime, dt.datetime]:
    """The instants a calendar day opens and closes in one zone.

    Half-open: the end is the start of the next day, so a row stamped 23:59:59
    belongs to the day it happened on and none is counted twice.

    The end is built from the next calendar day rather than by adding 24 hours.
    A day the zone shifts its offset is 23 or 25 hours long, and a fixed duration
    lands an hour inside or past midnight on those two days a year.
    """
    start = dt.datetime.combine(day, dt.time.min, tzinfo=zone)
    end = dt.datetime.combine(day + dt.timedelta(days=1), dt.time.min, tzinfo=zone)
    return start, end


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


def _as_date(parsed: dt.datetime | dt.date) -> dt.date:
    return parsed.date() if isinstance(parsed, dt.datetime) else parsed


def _is_date_column(column: InstrumentedAttribute) -> bool:
    return isinstance(column.type, sa.Date) and not isinstance(column.type, sa.DateTime)


def _criterion(column: InstrumentedAttribute, value: str, *, end: bool, zone: ZoneInfo | None) -> ColumnElement[bool]:
    """One bound's comparison, matched to the column's type and the bound's own.

    A `Date` column compared against an aware `datetime` makes Postgres cast the
    bound in the session `TimeZone`, so `2026-08-20` resolves to the 19th on any
    session west of UTC and the inclusive range this module promises silently
    loses a day at each end. Comparing a date against a date has no zone in it,
    so the zone is not consulted there.

    A bare day on a timestamp column is the day's span in `zone`. Opening a
    range it is the instant that day begins; closing one it is everything
    strictly before the next day begins, since an inclusive compare against
    midnight would keep only rows stamped exactly then.

    A bound that carries a time is an edge the caller placed, so it is left
    exactly as written at both ends. Widening a midnight end by a day would
    take in the whole day after it.
    """
    parsed = _parse_bound(value)
    if _is_date_column(column):
        as_written = _as_date(parsed)
        return column <= as_written if end else column >= as_written
    if isinstance(parsed, dt.datetime):
        return column <= parsed if end else column >= parsed
    if zone is None:
        raise TypeError(f'{column} stores instants, so a bare-day bound on it needs a zone')
    opens, closes = day_bounds(parsed, zone)
    return column < closes if end else column >= opens


def apply_date_bounds(
    query: Select,
    column: InstrumentedAttribute,
    start_date: str | None,
    end_date: str | None,
    timezone: str | None = None,
) -> Select:
    """Narrow to rows whose `column` falls within the bounds, or leave it alone.

    `timezone` is required for a timestamp column and ignored for a `Date` one.
    """
    zone = ZoneInfo(timezone) if timezone is not None else None
    if start_date is not None:
        query = query.where(_criterion(column, start_date, end=False, zone=zone))
    if end_date is not None:
        query = query.where(_criterion(column, end_date, end=True, zone=zone))
    return query
