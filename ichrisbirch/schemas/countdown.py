from datetime import datetime

from pydantic import BaseModel


class CountdownConfig(BaseModel):
    """Base config class for Task models"""

    class Config:
        orm_mode = True  # must be set for mapping to SQLAlchemy


class CountdownCreate(CountdownConfig):
    """Pydantic model for creating a task"""

    name: str
    notes: str | None
    due_date: datetime


class Countdown(CountdownConfig):
    """Pydantic model for a task"""

    id: int
    name: str
    notes: str | None
    due_date: datetime


class CountdownUpdate(CountdownConfig):
    """Pydantic model for updating a task"""

    name: str | None
    notes: str | None
    due_date: datetime | None
