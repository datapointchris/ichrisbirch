import logging
from datetime import datetime

import pendulum
from pydantic import BaseModel, validator

logger = logging.getLogger(__name__)


class EventConfig(BaseModel):
    class Config:
        orm_mode = True  # must be set for mapping to SQLAlchemy


class EventCreate(EventConfig):
    name: str
    date: datetime
    venue: str
    url: str | None
    cost: float
    attending: bool
    notes: str | None

    @validator('date', pre=True)
    def convert_string_date_to_utc_datetime(cls, v):
        """Require string or datetime
        Datetime from form comes in a string without timezone
        Pendulum will parse a string without a timezone, but will assign UTC
        Pendulum default includes timezone, datetime does not
        """
        logger.debug(f'date validator in: {v}, {type(v)}')
        if isinstance(v, datetime):
            dt = pendulum.instance(v)
        else:  # assume string, try to parse anything
            dt = pendulum.parser.parse(v)
        logger.debug(f'date validator out: {dt}, {type(dt)}')
        return dt


class Event(EventConfig):
    id: int
    name: str
    date: datetime
    venue: str
    url: str | None
    cost: float
    attending: bool
    notes: str | None


class EventUpdate(EventConfig):
    name: str | None
    date: datetime | None
    venue: str | None
    url: str | None
    cost: float | None
    attending: bool | None
    notes: str | None
