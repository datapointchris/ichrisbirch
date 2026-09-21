import datetime as dt

from pydantic import BaseModel
from pydantic import ConfigDict

from ichrisbirch.schemas.not_null import NotNull


class DurationConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class DurationNoteCreate(DurationConfig):
    date: dt.date
    content: str


class DurationNote(DurationConfig):
    id: int
    duration_id: int
    date: dt.date
    content: str


class DurationNoteUpdate(DurationConfig):
    date: NotNull[dt.date] = None
    content: NotNull[str] = None


class DurationCreate(DurationConfig):
    name: str
    start_date: dt.date
    end_date: dt.date | None = None
    notes: str | None = None
    color: str | None = None


class Duration(DurationConfig):
    id: int
    name: str
    start_date: dt.date
    end_date: dt.date | None = None
    notes: str | None = None
    color: str | None = None
    duration_notes: list[DurationNote] = []


class DurationUpdate(DurationConfig):
    name: NotNull[str] = None
    start_date: NotNull[dt.date] = None
    end_date: dt.date | None = None
    notes: str | None = None
    color: str | None = None
