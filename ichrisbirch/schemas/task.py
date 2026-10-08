import datetime as dt
from typing import Annotated

from pydantic import AwareDatetime
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from ichrisbirch.schemas.not_null import NotNull

WindowDays = Annotated[int, Field(ge=1)]


class TaskConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TaskCreate(TaskConfig):
    name: str
    notes: str | None = None
    category: str
    window_days: WindowDays | None = Field(None, description="Days until the task sorts as due. The category's window when omitted.")
    pinned: bool = False


class Task(TaskConfig):
    id: int
    name: str
    notes: str | None = None
    category: str
    rank_at: dt.datetime
    window_days: int
    pinned: bool
    autotask_id: int | None = None
    add_date: dt.datetime
    complete_date: dt.datetime | None = None
    drop_date: dt.datetime | None = None
    drop_reason: str | None = None


class TaskUpdate(TaskConfig):
    name: NotNull[str] = None
    notes: str | None = None
    category: NotNull[str] = None
    rank_at: NotNull[AwareDatetime] = None
    window_days: NotNull[WindowDays] = None
    pinned: NotNull[bool] = None
    add_date: NotNull[AwareDatetime] = None
    complete_date: AwareDatetime | None = None
    drop_date: AwareDatetime | None = None
    drop_reason: str | None = None


class TaskDrop(TaskConfig):
    reason: str | None = None


class TaskCompleted(TaskConfig):
    id: int
    name: str
    notes: str | None = None
    category: str
    window_days: int
    autotask_id: int | None = None
    add_date: dt.datetime
    complete_date: dt.datetime

    @property
    def days_to_complete(self) -> int:
        return max((self.complete_date - self.add_date).days, 1)

    @property
    def time_to_complete(self) -> str:
        weeks, days = divmod(self.days_to_complete, 7)
        return f'{weeks} weeks, {days} days'


class TaskCategory(TaskConfig):
    name: str
    window_days: int


class TaskCategoryUpdate(TaskConfig):
    window_days: NotNull[WindowDays] = None
