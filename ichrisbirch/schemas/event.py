from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict

from ichrisbirch.schemas.iana_zone import IanaZone
from ichrisbirch.schemas.not_null import NotNull
from ichrisbirch.schemas.wall_clock import WallClock


class EventConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class EventCreate(EventConfig):
    name: str
    date: WallClock
    timezone: IanaZone = 'UTC'
    venue: str
    url: str | None = None
    cost: float
    attending: bool
    notes: str | None = None


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
    name: NotNull[str] = None
    date: NotNull[WallClock] = None
    timezone: NotNull[IanaZone] = None
    venue: NotNull[str] = None
    url: str | None = None
    cost: NotNull[float] = None
    attending: NotNull[bool] = None
    notes: str | None = None
