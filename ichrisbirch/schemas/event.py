from datetime import datetime
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfoNotFoundError

import structlog
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import field_validator

logger = structlog.get_logger()


def validate_iana_timezone(v: str | None) -> str | None:
    """An IANA name, not an offset — the offset for a future date is not knowable yet.

    None passes through for the partial update, where an omitted field means unchanged.
    """
    if v is None:
        return v
    try:
        ZoneInfo(v)
    except (ZoneInfoNotFoundError, ValueError) as e:
        raise ValueError(f'{v!r} is not an IANA timezone name, e.g. America/New_York') from e
    return v


def strip_offset(v):
    """Drop any offset from an incoming date, keeping the wall clock it was written with.

    The date is a reading on a clock at the venue and `timezone` says which clock. A
    caller that sends an offset anyway is describing the same wall time, so the reading
    is kept and the offset discarded rather than being converted into another zone.
    """
    if isinstance(v, datetime):
        return v.replace(tzinfo=None)
    return v


class EventConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class EventCreate(EventConfig):
    name: str
    date: datetime
    timezone: str = 'UTC'
    venue: str
    url: str | None = None
    cost: float
    attending: bool
    notes: str | None = None

    _strip_offset = field_validator('date', mode='after')(strip_offset)
    _check_timezone = field_validator('timezone')(validate_iana_timezone)


class Event(EventConfig):
    id: int
    name: str
    date: datetime
    timezone: str
    venue: str
    url: str | None = None
    cost: float
    attending: bool
    notes: str | None = None


class EventUpdate(EventConfig):
    name: str | None = None
    date: datetime | None = None
    timezone: str | None = None
    venue: str | None = None
    url: str | None = None
    cost: float | None = None
    attending: bool | None = None
    notes: str | None = None

    _strip_offset = field_validator('date', mode='after')(strip_offset)
    _check_timezone = field_validator('timezone')(validate_iana_timezone)
