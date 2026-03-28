from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class ProjectItemConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProjectItemCreate(ProjectItemConfig):
    title: str
    notes: str | None = None
    project_ids: list[int]


class ProjectItem(ProjectItemConfig):
    id: int
    title: str
    notes: str | None = None
    completed: bool
    archived: bool
    created_at: datetime
    updated_at: datetime


class ProjectItemUpdate(ProjectItemConfig):
    title: str | None = None
    notes: str | None = None
    completed: bool | None = None
    archived: bool | None = None


class ProjectItemDetail(ProjectItemConfig):
    """Extended view with membership and dependency info."""

    id: int
    title: str
    notes: str | None = None
    completed: bool
    archived: bool
    created_at: datetime
    updated_at: datetime
    project_ids: list[int]
    dependency_ids: list[int]


class ProjectItemInProject(ProjectItemConfig):
    """Item as seen within a project context, includes position."""

    id: int
    title: str
    notes: str | None = None
    completed: bool
    archived: bool
    created_at: datetime
    updated_at: datetime
    position: int


class ProjectItemReorder(ProjectItemConfig):
    project_id: int
    position: int


class ProjectItemMembershipCreate(ProjectItemConfig):
    project_id: int


class ProjectItemDependencyCreate(ProjectItemConfig):
    depends_on_id: int
