from datetime import datetime
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
    completed_at: datetime | None = None
    position: int
    created_at: datetime


class ProjectItemTaskUpdate(ProjectItemTaskConfig):
    title: NotNull[str] = None
    completed: NotNull[bool] = None
    position: NotNull[int] = None
