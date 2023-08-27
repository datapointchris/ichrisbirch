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
    def convert_string_date_to_datetime(cls, v):
        logger.debug(f'date validator input: {v}, {type(v)}')
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            # This is the correct way to do it
            dt = pendulum.parser.parse(v)
            logger.debug(f'date validator returning: {dt}, {type(dt)}')
            return dt
        raise ValueError('Event creation date must be a datetime or string')


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
