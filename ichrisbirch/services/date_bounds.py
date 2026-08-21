"""Date-range narrowing for the list reads whose rows carry a date.

Most apps store a timestamp their collection read has no other way to narrow by,
which leaves "what did I finish this week" to be answered by fetching everything
and cutting it up client-side. `data.md` § "Filtering is server-side" puts the
`WHERE` here instead, once, so the CLI and the web client share one definition of
what a bound means.

The semantics are the ones `/habits/completed/` established: both bounds are
inclusive, each narrows on its own so one without the other is an open-ended
range, and an unparsable value is a 422 rather than a silently ignored filter.

A bound compares against a nullable column, so a row with no date is outside
every range — an unread article is not "read before today", and an open task was
not "completed this week".
"""

import datetime as dt
from typing import Annotated

import pendulum
from fastapi import HTTPException
from fastapi import Query
from fastapi import status
from pendulum.parsing.exceptions import ParserError
from sqlalchemy import Select
from sqlalchemy.orm import InstrumentedAttribute

StartDate = Annotated[str | None, Query(description='Only rows dated on or after this ISO 8601 date')]
EndDate = Annotated[str | None, Query(description='Only rows dated on or before this ISO 8601 date')]


def _parse_bound(value: str) -> dt.datetime:
    try:
        parsed = pendulum.parse(value)
    except ParserError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f'Invalid date format: {e}') from e
    # pendulum.parse also answers durations and bare times, which would reach the
    # comparison as a type the column cannot be compared against and surface as a
    # 500 on what is a caller's mistake.
    if not isinstance(parsed, dt.datetime):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f'Invalid date format: {value!r} is not a date or datetime',
        )
    return parsed


def apply_date_bounds(query: Select, column: InstrumentedAttribute, start_date: str | None, end_date: str | None) -> Select:
    """Narrow to rows whose `column` falls within the bounds, or leave it alone."""
    if start_date is not None:
        query = query.where(column >= _parse_bound(start_date))
    if end_date is not None:
        query = query.where(column <= _parse_bound(end_date))
    return query
