from datetime import date

from pydantic import BaseModel
from pydantic import ConfigDict

from ichrisbirch.schemas.not_null import NotNull


class CountdownConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CountdownCreate(CountdownConfig):
    name: str
    notes: str | None = None
    due_date: date


class Countdown(CountdownConfig):
    id: int
    name: str
    notes: str | None = None
    due_date: date


class CountdownUpdate(CountdownConfig):
    name: NotNull[str] = None
    notes: str | None = None
    due_date: NotNull[date] = None
