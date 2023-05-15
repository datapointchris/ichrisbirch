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
    category: TaskCategory
    priority: int
    notes: str | None
    frequency: TaskFrequency
    first_run_date: datetime
    last_run_date: datetime
    run_count: int


class AutoTaskUpdate(AutoTaskConfig):
    """Pydantic model for updating a task"""

    name: str | None
    category: TaskCategory | None
    priority: int | None
    notes: str | None
    frequency: TaskFrequency | None
