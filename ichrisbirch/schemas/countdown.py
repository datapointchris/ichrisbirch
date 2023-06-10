from datetime import date

from pydantic import BaseModel


class CountdownConfig(BaseModel):
    class Config:
        orm_mode = True  # must be set for mapping to SQLAlchemy


class CountdownCreate(CountdownConfig):
    name: str
    notes: str | None
    due_date: date


class Countdown(CountdownConfig):
    id: int
    name: str
    notes: str | None
    due_date: date


class CountdownUpdate(CountdownConfig):
    name: str | None
    notes: str | None
    due_date: date | None
