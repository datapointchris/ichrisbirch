from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict


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
    position: int
    created_at: datetime


class ProjectItemTaskUpdate(ProjectItemTaskConfig):
    title: str | None = None
    completed: bool | None = None
    position: int | None = None
