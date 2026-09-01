from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import computed_field

from ichrisbirch.schemas.project import Project
from ichrisbirch.schemas.project_item_task import ProjectItemTask
from ichrisbirch.services.project_item_status import derive_item_status


class ProjectItemConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProjectItemStatusFields(ProjectItemConfig):
    """The two stored booleans, and the one word every item view renders from them.

    Each view deriving the word for itself is how the text output came to show a
    `status` the JSON did not carry. Serializing it means both doors answer with
    the same document, and a consumer reads a status without reimplementing the
    archived-beats-completed precedence.
    """

    completed: bool
    archived: bool

    @computed_field  # type: ignore[prop-decorator]
    @property
    def status(self) -> str:
        return derive_item_status(self.archived, self.completed)


# What a caller may pass where an item or a project is named. An item answers to
# its UUID or its number, a project to its UUID or its unique name, and the API
# resolves either — see ichrisbirch.services.project_refs.
#
# `str` is in the item union deliberately: a CLI forwards whatever the user typed
# without parsing it, so a number arrives as "42" rather than 42. Widening here
# rather than in each client keeps the one place that tells a key from a handle
# in the resolver.
ItemRef = UUID | int | str
ProjectRef = UUID | str


class ProjectItemCreate(ProjectItemConfig):
    id: UUID | None = None
    title: str
    notes: str | None = None
    repo: str | None = None
    project_ids: list[ProjectRef]


class ProjectItem(ProjectItemStatusFields):
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
    number: int
    title: str
    notes: str | None = None
    repo: str | None = None
    # Null where the completion time is unknown: never finished, or finished by a
    # write that recorded none. Every reader handles it.
    completed_at: datetime | None = None
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


class ProjectItemDetail(ProjectItemStatusFields):
    """Extended view with membership and dependency info."""

    id: UUID
    number: int
    title: str
    notes: str | None = None
    repo: str | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    projects: list[Project]
    dependency_ids: list[UUID]


class ProjectItemInProject(ProjectItemStatusFields):
    """Item as seen within a project context, includes position."""

    id: UUID
    number: int
    title: str
    notes: str | None = None
    repo: str | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    position: int


class ProjectItemReorder(ProjectItemConfig):
    project_id: ProjectRef
    position: int


class ProjectItemMembershipCreate(ProjectItemConfig):
    project_id: ProjectRef


class ProjectItemDependencyCreate(ProjectItemConfig):
    depends_on_id: ItemRef
