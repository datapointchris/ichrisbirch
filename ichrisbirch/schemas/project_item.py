from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict

from ichrisbirch.schemas.project import Project
from ichrisbirch.schemas.project_item_task import ProjectItemTask


class ProjectItemConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProjectItemCreate(ProjectItemConfig):
    id: UUID | None = None
    title: str
    notes: str | None = None
    repo: str | None = None
    project_ids: list[UUID]


class ProjectItem(ProjectItemConfig):
    """An item always travels with the projects it belongs to.

    An item title on its own ("Glove 80") names a thing without saying what work
    it is part of, so every list response carries its membership rather than
    making each consumer fetch it per item.

    Dependencies and sub-tasks ride along for the same reason, and because the
    alternative is quadratic: a client reconciling the whole list had to issue
    two requests per item to collect them, which was 122 serial round trips and
    six seconds for todoui at 60 items. Eager-load `dependencies` and `tasks` in
    any endpoint that returns a list of these.
    """

    id: UUID
    title: str
    notes: str | None = None
    repo: str | None = None
    completed: bool
    archived: bool
    created_at: datetime
    updated_at: datetime
    projects: list[Project] = []
    dependency_ids: list[UUID] = []
    tasks: list[ProjectItemTask] = []


class ProjectItemUpdate(ProjectItemConfig):
    title: str | None = None
    notes: str | None = None
    repo: str | None = None
    completed: bool | None = None
    archived: bool | None = None


class ProjectItemDetail(ProjectItemConfig):
    """Extended view with membership and dependency info."""

    id: UUID
    title: str
    notes: str | None = None
    repo: str | None = None
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
    repo: str | None = None
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
