from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict

from ichrisbirch.schemas.project import Project


class ProjectItemConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProjectItemCreate(ProjectItemConfig):
    title: str
    notes: str | None = None
    project_ids: list[UUID]


class ProjectItem(ProjectItemConfig):
    id: UUID
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

    id: UUID
    title: str
    notes: str | None = None
    completed: bool
    archived: bool
    created_at: datetime
    updated_at: datetime
    projects: list[Project]
    dependency_ids: list[UUID]


class ProjectItemInProject(ProjectItemConfig):
    """Item as seen within a project context, includes position."""

    id: UUID
    title: str
    notes: str | None = None
    completed: bool
    archived: bool
    created_at: datetime
    updated_at: datetime
    position: int


class ProjectItemReorder(ProjectItemConfig):
    project_id: UUID
    position: int


class ProjectItemMembershipCreate(ProjectItemConfig):
    project_id: UUID


class ProjectItemDependencyCreate(ProjectItemConfig):
    depends_on_id: UUID
