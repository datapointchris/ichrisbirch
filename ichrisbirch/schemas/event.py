from datetime import datetime

from pydantic import BaseModel, validator


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
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            return datetime.strptime(v, '%Y-%m-%dT%H:%M:%S')
        raise ValueError("datetime or string in proper format required")


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
