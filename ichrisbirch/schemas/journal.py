from datetime import datetime

import structlog
from pydantic import BaseModel
from pydantic import ConfigDict

logger = structlog.get_logger()


class JournalEntryConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class JournalEntryCreate(JournalEntryConfig):
    title: str
    date: datetime
    content: str
    feeling: int


class JournalEntry(JournalEntryConfig):
    id: int
    title: str
    date: datetime
    content: str
    feeling: int


class JournalEntryUpdate(JournalEntryConfig):
    title: str | None = None
    date: datetime | None = None
    content: str | None = None
    feeling: int | None = None
