from datetime import datetime

from pydantic import AwareDatetime
from pydantic import BaseModel
from pydantic import ConfigDict

from ichrisbirch.schemas.not_null import NotNull


class TaskConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TaskCreate(TaskConfig):
    name: str
    notes: str | None = None
    category: str
    priority: int = 1


class Task(TaskConfig):
    id: int
    name: str
    notes: str | None = None
    category: str
    priority: int
    add_date: datetime
    complete_date: datetime | None = None


class TaskUpdate(TaskConfig):
    name: NotNull[str] = None
    notes: str | None = None
    category: NotNull[str] = None
    priority: NotNull[int] = None
    add_date: NotNull[AwareDatetime] = None
    complete_date: AwareDatetime | None = None


class TaskCompleted(TaskConfig):
    id: int
    name: str
    notes: str | None = None
    category: str
    priority: int
    add_date: datetime
    complete_date: datetime

    @property
    def days_to_complete(self) -> int:
        return max((self.complete_date - self.add_date).days, 1)

    @property
    def time_to_complete(self) -> str:
        weeks, days = divmod(self.days_to_complete, 7)
        return f'{weeks} weeks, {days} days'
