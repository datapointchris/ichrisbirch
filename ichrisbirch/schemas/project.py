import datetime as dt
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator
from pydantic import BaseModel
from pydantic import ConfigDict

from ichrisbirch.schemas.not_null import NotNull

ITEMS_ROUTE_SUFFIX = '/items'


def refuse_items_route_suffix(name: str) -> str:
    """A project is addressed by name in the path, so `x/items` would read as project `x`'s items."""
    if name.endswith(ITEMS_ROUTE_SUFFIX):
        raise ValueError(f'cannot end in {ITEMS_ROUTE_SUFFIX!r}, which /projects/<name>/items/ reads as an item list')
    return name


ProjectName = Annotated[str, AfterValidator(refuse_items_route_suffix)]


class ProjectConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProjectCreate(ProjectConfig):
    """`status` is accepted on create so a client holding a finished project can
    push it as it stands — todoui creates offline and syncs later, and a project
    it completed while disconnected must not come back as active."""

    id: UUID | None = None
    name: ProjectName
    description: str | None = None
    kind: str = 'life'
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
    closed_at: dt.datetime | None = None
    position: int
    created_at: dt.datetime


class ProjectUpdate(ProjectConfig):
    """`closed_at` is absent deliberately: the server stamps it on the transition
    into a terminal status and clears it on reopen, so it cannot drift from the
    status it describes."""

    name: NotNull[ProjectName] = None
    description: str | None = None
    kind: NotNull[str] = None
    status: NotNull[str] = None
    status_reason: str | None = None
    position: NotNull[int] = None


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
    closed_at: dt.datetime | None = None
    position: int
    created_at: dt.datetime
    item_count: int
    open_count: int
    completed_count: int
    repos: list[str] = []
