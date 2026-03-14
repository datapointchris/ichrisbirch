from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class AutoTaskConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AutoTaskCreate(AutoTaskConfig):
    name: str
    notes: str | None = None
    category: str
    priority: int
    frequency: str
    max_concurrent: int | None = None


class AutoTask(AutoTaskConfig):
    id: int
    name: str
    category: str
    priority: int
    notes: str | None = None
    frequency: str
    max_concurrent: int
    first_run_date: datetime
    last_run_date: datetime
    run_count: int


class AutoTaskUpdate(AutoTaskConfig):
    name: str | None = None
    category: str | None = None
    priority: int | None = None
    notes: str | None = None
    frequency: str | None = None
    max_concurrent: int | None = None
