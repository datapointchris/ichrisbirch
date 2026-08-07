from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class PatternConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PatternCreate(PatternConfig):
    message: str
    # Optional so a capture is one argument, but settable so the dotfiles JSONL
    # entries import at the time they were written rather than the time of import.
    recorded_at: datetime | None = None


class Pattern(PatternConfig):
    id: int
    message: str
    recorded_at: datetime


class PatternUpdate(PatternConfig):
    message: str | None = None
    recorded_at: datetime | None = None
