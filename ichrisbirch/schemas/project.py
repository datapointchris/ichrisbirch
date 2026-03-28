from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class ProjectConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProjectCreate(ProjectConfig):
    name: str
    position: int = 0


class Project(ProjectConfig):
    id: int
    name: str
    position: int
    created_at: datetime


class ProjectUpdate(ProjectConfig):
    name: str | None = None
    position: int | None = None


class ProjectWithItemCount(ProjectConfig):
    id: int
    name: str
    position: int
    created_at: datetime
    item_count: int
