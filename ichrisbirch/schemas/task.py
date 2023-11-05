from datetime import datetime

from pydantic import BaseModel, ConfigDict

from ichrisbirch.models.task import TaskCategory


class TaskConfig(BaseModel):
    """Base config class for Task models"""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class TaskCreate(TaskConfig):
    """Pydantic model for creating a task"""

    name: str
    notes: str | None = None
    category: TaskCategory
    priority: int


class Task(TaskConfig):
    """Pydantic model for a task"""

    id: int
    name: str
    notes: str | None = None
    category: TaskCategory
    priority: int
    add_date: datetime
    complete_date: datetime | None = None


class TaskUpdate(TaskConfig):
    """Pydantic model for updating a task"""

    name: str | None = None
    notes: str | None = None
    category: TaskCategory | None = None
    priority: int | None = None
    add_date: datetime | None = None
    complete_date: datetime | None = None


class TaskCompleted(TaskConfig):
    """Pydantic model for a task"""

    id: int
    name: str
    notes: str | None = None
    category: TaskCategory
    priority: int
    add_date: datetime
    complete_date: datetime
