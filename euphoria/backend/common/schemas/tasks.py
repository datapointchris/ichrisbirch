from datetime import datetime
from pydantic import BaseModel


class TaskCreate(BaseModel):
    name: str
    notes: str | None
    category: str
    priority: int


class Task(BaseModel):
    id: int
    name: str
    notes: str | None
    category: str
    priority: int
    add_date: datetime
    complete_date: datetime | None

    class Config:  # must be set for mapping to SQLAlchemy
        orm_mode = True


class TaskUpdate(Task):
    ...
