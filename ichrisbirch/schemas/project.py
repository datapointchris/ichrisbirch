from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict


class ProjectConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProjectCreate(ProjectConfig):
    id: UUID | None = None
    name: str
    description: str | None = None
    kind: str = 'build'
    position: int = 0


class Project(ProjectConfig):
    id: UUID
    name: str
    description: str | None = None
    kind: str
    position: int
    created_at: datetime


class ProjectUpdate(ProjectConfig):
    name: str | None = None
    description: str | None = None
    kind: str | None = None
    position: int | None = None


class ProjectWithItemCount(ProjectConfig):
    """A project plus the counts that say whether it still has work in it.

    The three counts partition `item_count`: archived beats completed, so an
    archived item is neither open nor completed and
    `item_count - open_count - completed_count` is the archived remainder.

    `repos` is derived from the items, never stored: the item's `repo` tag is the
    single source of truth for what code a piece of work touches, and a project
    column beside it would be a second copy free to drift. A project spanning an
    API, a CLI, and a TUI lists all three.
    """

    id: UUID
    name: str
    description: str | None = None
    kind: str
    position: int
    created_at: datetime
    item_count: int
    open_count: int
    completed_count: int
    repos: list[str] = []
