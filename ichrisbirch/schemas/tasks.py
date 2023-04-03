from datetime import datetime

from pydantic import BaseModel

from ichrisbirch.models.tasks import TaskCategory


class TaskConfig(BaseModel):
    """Base config class for Task models"""

    class Config:
        orm_mode = True  # must be set for mapping to SQLAlchemy
        use_enum_values = True


class TaskCreate(TaskConfig):
    """Pydantic model for creating a task"""

    name: str
    notes: str | None
    category: TaskCategory
    priority: int


class Task(TaskConfig):
    """Pydantic model for a task"""

    id: int
    name: str
    notes: str | None
    category: TaskCategory
    priority: int
    add_date: datetime
    complete_date: datetime | None


class TaskUpdate(TaskConfig):
    """Pydantic model for updating a task"""

    name: str | None
    notes: str | None
    category: TaskCategory | None
    priority: int | None
    add_date: datetime | None
    complete_date: datetime | None


class TaskCompleted(TaskConfig):
    """Pydantic model for a task"""

    id: int
    name: str
    notes: str | None
    category: TaskCategory
    priority: int
    add_date: datetime
    complete_date: datetime
