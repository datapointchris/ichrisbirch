from datetime import datetime

from pydantic import BaseModel

from ichrisbirch.models.autotask import TaskFrequency
from ichrisbirch.models.task import TaskCategory


class AutoTaskConfig(BaseModel):
    class Config:
        orm_mode = True  # must be set for mapping to SQLAlchemy
        use_enum_values = True


class AutoTaskCreate(AutoTaskConfig):
    name: str
    notes: str | None
    category: TaskCategory
    priority: int
    frequency: TaskFrequency


class AutoTask(AutoTaskConfig):
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
    name: str | None
    category: TaskCategory | None
    priority: int | None
    notes: str | None
    frequency: TaskFrequency | None
