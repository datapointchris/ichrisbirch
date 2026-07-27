"""Project item position compaction service.

Dense-ranks a project's item memberships to contiguous positions 0..N-1. Used
by the `/project-items/{id}/reorder/` endpoint so that moving one item shifts
its siblings instead of colliding with them.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch.models.project import ProjectItemMembership


def load_project_memberships_in_order(session: Session, project_id: UUID) -> list[ProjectItemMembership]:
    """Return a project's memberships ordered by position, ties broken by item creation.

    The tie-break matters: `position` carries no unique constraint, so a project
    whose positions have already collided would otherwise resequence in whatever
    order the database happened to return.
    """
    query = (
        select(ProjectItemMembership)
        .join(models.ProjectItem, models.ProjectItem.id == ProjectItemMembership.item_id)
        .where(ProjectItemMembership.project_id == project_id)
        .order_by(ProjectItemMembership.position.asc(), models.ProjectItem.created_at.asc())
    )
    return list(session.scalars(query).all())


def move_membership_to_position(session: Session, project_id: UUID, item_id: UUID, position: int) -> int:
    """Move one item to `position` and dense-rank the whole project to 0..N-1.

    `position` is clamped into range rather than rejected, so a caller asking for
    the end of a list does not need to know its length. Returns the position the
    item actually landed on. Does not commit — the caller owns the transaction.
    """
    memberships = load_project_memberships_in_order(session, project_id)
    moving = next(m for m in memberships if m.item_id == item_id)

    remaining = [m for m in memberships if m.item_id != item_id]
    landed = max(0, min(position, len(remaining)))
    remaining.insert(landed, moving)

    for new_position, membership in enumerate(remaining):
        membership.position = new_position

    return landed


def compact_project_positions(session: Session, project_id: UUID) -> int:
    """Dense-rank a project's positions to 0..N-1 without moving anything.

    Repairs a project whose positions have collided or gone sparse. Returns the
    number of memberships resequenced. Does not commit.
    """
    memberships = load_project_memberships_in_order(session, project_id)
    for new_position, membership in enumerate(memberships):
        membership.position = new_position
    return len(memberships)
