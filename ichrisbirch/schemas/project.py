from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict


class ProjectConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProjectCreate(ProjectConfig):
    name: str
    description: str | None = None
    position: int = 0


class Project(ProjectConfig):
    id: UUID
    name: str
    description: str | None = None
    position: int
    created_at: datetime


class ProjectUpdate(ProjectConfig):
    name: str | None = None
    description: str | None = None
    position: int | None = None


class ProjectWithItemCount(ProjectConfig):
    id: UUID
    name: str
    description: str | None = None
    position: int
    created_at: datetime
    item_count: int
