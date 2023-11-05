from datetime import date

from pydantic import BaseModel, ConfigDict


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
    name: str | None = None
    notes: str | None = None
    due_date: date | None = None
