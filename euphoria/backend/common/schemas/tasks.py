from datetime import datetime
from zoneinfo import ZoneInfo
from pydantic import BaseModel


class TaskCreate(BaseModel):
    name: str
    category: str
    priority: int


class Task(BaseModel):
    id: int
    name: str
    category: str
    priority: int
    add_date: datetime
    complete_date: datetime | None

    class Config:  # must be set for mapping to SQLAlchemy
        orm_mode = True


class TaskUpdate(Task):
    ...
