from datetime import datetime

from pydantic import BaseModel


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
