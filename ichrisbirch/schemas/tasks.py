from datetime import datetime

from pydantic import BaseModel

from ichrisbirch.models.tasks import TaskCategory


class TaskCreate(BaseModel):
    """Pydantic model for creating a task"""

    name: str
    notes: str | None
    category: str
    priority: int


class Task(BaseModel):
    """Pydantic model for a task"""

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
    """Pydantic model for updating a task"""

    ...
