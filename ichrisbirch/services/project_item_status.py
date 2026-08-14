"""Derived-status filtering for project items.

Two stored booleans, `completed` and `archived`, present as three mutually
exclusive states plus `all`. Both list endpoints read through here — the flat
`/project-items/` and the project-scoped `/projects/{id}/items/` — because a
scope selects which rows it returns and not which states, so the two paths
answer `status` identically. See `cli-design.md` § "A scope selects which rows,
not which states".
"""

from fastapi import HTTPException
from fastapi import status
from sqlalchemy import Select

from ichrisbirch import models
from ichrisbirch.models.project import ITEM_STATUSES

# Not a status, so it is not in ITEM_STATUSES: `all` is the absence of the
# filter, and including it would make it look assignable to an item.
ALL_STATUSES = 'all'


def apply_status_filter(query: Select, item_status: str) -> Select:
    """Narrow to one derived status, or leave the query alone for `all`.

    `archived` beats `completed`, matching the precedence the item counts and
    every client render — so `completed` means finished and still in view, and an
    item that was completed and then archived answers to `archived` alone. Two
    booleans, three states, and no combination is reachable twice.
    """
    if item_status == ALL_STATUSES:
        return query
    if item_status == 'archived':
        return query.where(models.ProjectItem.archived == True)  # noqa: E712
    query = query.where(models.ProjectItem.archived == False)  # noqa: E712
    return query.where(models.ProjectItem.completed == (item_status == 'completed'))


def validate_item_status(item_status: str) -> None:
    """Reject an unknown status by name rather than answering with an empty list.

    No lookup table to check against, unlike a project's: an item's status is
    derived from booleans, so the vocabulary is a constant.
    """
    if item_status not in (*ITEM_STATUSES, ALL_STATUSES):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f'Unknown item status {item_status!r}. Known statuses: {", ".join(ITEM_STATUSES)}, all',
        )
