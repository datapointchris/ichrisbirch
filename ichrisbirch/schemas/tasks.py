from datetime import datetime
from pydantic import BaseModel
from ichrisbirch.models.tasks import TaskCategory


class TaskCreate(BaseModel):
    name: str
    notes: str | None
    category: str
    priority: int


class Task(BaseModel):
    id: int
    name: str
    notes: str | None
    category: TaskCategory
    priority: int
    add_date: datetime
    complete_date: datetime | None

    class Config:
        orm_mode = True  # must be set for mapping to SQLAlchemy
        use_enum_values = True


class TaskUpdate(Task):
    ...
