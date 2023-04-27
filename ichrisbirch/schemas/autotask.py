from datetime import datetime

from pydantic import BaseModel

from ichrisbirch.models.autotask import TaskFrequency
from ichrisbirch.models.task import TaskCategory


class AutoTaskConfig(BaseModel):
    """Base config class for Task models"""

    class Config:
        orm_mode = True  # must be set for mapping to SQLAlchemy
        use_enum_values = True


class AutoTaskCreate(AutoTaskConfig):
    """Pydantic model for creating a task"""

    name: str
    notes: str | None
    category: TaskCategory
    priority: int
    frequency: TaskFrequency


class AutoTask(AutoTaskConfig):
    """Pydantic model for a task"""

    id: int
    name: str
    notes: str | None
    category: TaskCategory
    priority: int
    start_date: datetime
    last_run_date: datetime
    frequency: TaskFrequency


class AutoTaskUpdate(AutoTaskConfig):
    """Pydantic model for updating a task"""

    name: str | None
    notes: str | None
    category: TaskCategory | None
    priority: int | None
    start_date: datetime | None
    last_run_date: datetime | None
    frequency: TaskFrequency | None
