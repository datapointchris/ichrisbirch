import logging
from datetime import datetime

import pendulum
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import field_validator

logger = logging.getLogger(__name__)


class EventConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class EventCreate(EventConfig):
    name: str
    date: datetime
    venue: str
    url: str | None = None
    cost: float
    attending: bool
    notes: str | None = None

    @field_validator('date', mode='before')
    @classmethod
    def convert_string_date_to_utc_datetime(cls, v):
        """Require string or datetime Datetime from form comes in a string without timezone Pendulum will parse a string without a timezone,
        but will assign UTC Pendulum default includes timezone, datetime does not.
        """
        logger.debug(f'date validator in: {v}, {type(v)}')
        if isinstance(v, datetime):
            dt = pendulum.instance(v)
        else:  # assume string, try to parse anything
            dt = pendulum.parse(v)

        # Ensure the datetime is in UTC
        if dt.timezone_name != 'UTC':
            dt = dt.in_timezone('UTC')

        logger.debug(f'date validator out: {dt}, {type(dt)}')
        return dt


class Event(EventConfig):
    id: int
    name: str
    date: datetime
    venue: str
    url: str | None = None
    cost: float
    attending: bool
    notes: str | None = None


class EventUpdate(EventConfig):
    name: str | None = None
    date: datetime | None = None
    venue: str | None = None
    url: str | None = None
    cost: float | None = None
    attending: bool | None = None
    notes: str | None = None
