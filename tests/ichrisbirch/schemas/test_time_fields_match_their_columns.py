"""A time field in a request schema takes the kind its column stores.

A timestamptz column holds a moment, so its field refuses a reading with no
offset. A Date column holds a calendar day, so its field refuses a time of day.
A naive timestamp column holds a wall clock, so its field keeps the reading and
drops any offset. Each `*Create` and `*Update` is walked against the model its
name points at, so a new time column is covered without being listed here.
"""

import datetime as dt
import inspect
from typing import Annotated

import pytest
import sqlalchemy as sa
from pydantic import BaseModel
from pydantic import TypeAdapter
from pydantic import ValidationError

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.database.base import Base

REQUEST_SCHEMAS = {
    name: cls
    for name, cls in inspect.getmembers(schemas, inspect.isclass)
    if name.endswith(('Create', 'Update')) and issubclass(cls, BaseModel)
}


def model_for(schema_name: str):
    return getattr(models, schema_name.removesuffix('Create').removesuffix('Update'), None)


def time_kind(column: sa.Column) -> str | None:
    if isinstance(column.type, sa.DateTime):
        return 'moment' if column.type.timezone else 'wall_clock'
    if isinstance(column.type, sa.Date):
        return 'day'
    return None


def time_fields(schema_name: str) -> list[tuple[str, str]]:
    model = model_for(schema_name)
    if model is None:
        return []
    # By attribute, not by table column: an attribute may be stored under another column name.
    columns = {attr.key: attr.columns[0] for attr in model.__mapper__.column_attrs}
    fields = REQUEST_SCHEMAS[schema_name].model_fields
    return [(field, kind) for field in fields if field in columns and (kind := time_kind(columns[field]))]


CASES = [(name, field, kind) for name in sorted(REQUEST_SCHEMAS) for field, kind in time_fields(name)]


def field_adapter(schema_name: str, field: str) -> TypeAdapter:
    """The field alone, so a Create schema's other required fields stay out of it."""
    info = REQUEST_SCHEMAS[schema_name].model_fields[field]
    return TypeAdapter(Annotated[info.annotation, info])


def cases_of(kind: str) -> list[tuple[str, str]]:
    return [(name, field) for name, field, case_kind in CASES if case_kind == kind]


def test_the_walk_reaches_every_kind():
    assert len(cases_of('moment')) >= 5, 'too few moment fields to be reading the schemas'
    assert len(cases_of('day')) >= 20, 'too few day fields to be reading the schemas'
    assert len(cases_of('wall_clock')) >= 2, 'the event date is missing from the walk'


def test_the_only_wall_clock_column_is_the_event_date():
    """A wall clock means nothing without the zone beside it, and `events.timezone` is the one zone column."""
    columns = [column for table in Base.metadata.tables.values() for column in table.columns]
    wall_clocks = {f'{column.table.name}.{column.name}' for column in columns if time_kind(column) == 'wall_clock'}

    assert wall_clocks == {'events.date'}


@pytest.mark.parametrize(('schema_name', 'field'), cases_of('moment'))
def test_a_moment_field_refuses_a_reading_with_no_offset(schema_name, field):
    adapter = field_adapter(schema_name, field)

    with pytest.raises(ValidationError):
        adapter.validate_python('2026-08-20T10:00:00')
    assert adapter.validate_python('2026-08-20T10:00:00-04:00') == dt.datetime(2026, 8, 20, 14, tzinfo=dt.UTC)


@pytest.mark.parametrize(('schema_name', 'field'), cases_of('day'))
def test_a_day_field_refuses_a_time_of_day(schema_name, field):
    adapter = field_adapter(schema_name, field)

    with pytest.raises(ValidationError):
        adapter.validate_python('2026-08-20T10:00:00-04:00')
    assert adapter.validate_python('2026-08-20') == dt.date(2026, 8, 20)


@pytest.mark.parametrize(('schema_name', 'field'), cases_of('wall_clock'))
def test_a_wall_clock_field_keeps_the_reading(schema_name, field):
    adapter = field_adapter(schema_name, field)

    assert adapter.validate_python('2026-08-20T19:00:00-04:00') == dt.datetime(2026, 8, 20, 19)
