from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict


class ProjectConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProjectCreate(ProjectConfig):
    """`status` is accepted on create so a client holding a finished project can
    push it as it stands — todoui creates offline and syncs later, and a project
    it completed while disconnected must not come back as active."""

    id: UUID | None = None
    name: str
    description: str | None = None
    kind: str = 'build'
    status: str = 'active'
    status_reason: str | None = None
    position: int = 0


class Project(ProjectConfig):
    id: UUID
    name: str
    description: str | None = None
    kind: str
    status: str
    status_reason: str | None = None
    closed_at: datetime | None = None
    position: int
    created_at: datetime


class ProjectUpdate(ProjectConfig):
    """`closed_at` is absent deliberately: the server stamps it on the transition
    into a terminal status and clears it on reopen, so it cannot drift from the
    status it describes."""

    name: str | None = None
    description: str | None = None
    kind: str | None = None
    status: str | None = None
    status_reason: str | None = None
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
    status: str
    status_reason: str | None = None
    closed_at: datetime | None = None
    position: int
    created_at: datetime
    item_count: int
    open_count: int
    completed_count: int
    repos: list[str] = []
