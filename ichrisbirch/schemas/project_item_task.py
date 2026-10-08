import datetime as dt
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict

from ichrisbirch.schemas.not_null import NotNull


class ProjectItemTaskConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProjectItemTaskCreate(ProjectItemTaskConfig):
    id: UUID | None = None
    title: str
    position: int = 0


class ProjectItemTask(ProjectItemTaskConfig):
    id: UUID
    item_id: UUID
    title: str
    completed: bool
    completed_at: dt.datetime | None = None
    position: int
    created_at: dt.datetime


class ProjectItemTaskUpdate(ProjectItemTaskConfig):
    title: NotNull[str] = None
    completed: NotNull[bool] = None
    position: NotNull[int] = None
