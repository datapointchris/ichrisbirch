from datetime import datetime

from pydantic import BaseModel, ConfigDict

from ichrisbirch.models.autotask import TaskFrequency
from ichrisbirch.models.task import TaskCategory


class AutoTaskConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class AutoTaskCreate(AutoTaskConfig):
    name: str
    notes: str | None = None
    category: TaskCategory
    priority: int
    frequency: TaskFrequency


class AutoTask(AutoTaskConfig):
    id: int
    name: str
    category: TaskCategory
    priority: int
    notes: str | None = None
    frequency: TaskFrequency
    first_run_date: datetime
    last_run_date: datetime
    run_count: int


class AutoTaskUpdate(AutoTaskConfig):
    name: str | None = None
    category: TaskCategory | None = None
    priority: int | None = None
    notes: str | None = None
    frequency: TaskFrequency | None = None
