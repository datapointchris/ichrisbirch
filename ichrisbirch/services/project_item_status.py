"""The derived status of a project item, in both directions.

Two stored booleans, `completed` and `archived`, present as three mutually
exclusive states plus `all`. Both list endpoints read through here — the flat
`/project-items/` and the project-scoped `/projects/{id}/items/` — because a
scope selects which rows it returns and not which states, so the two paths
answer `status` identically. See `cli-design.md` § "A scope selects which rows,
not which states".

`apply_status_filter` narrows a query to one status and `derive_item_status`
names one row's, so the set a filter returns is exactly the set whose derived
status matches it. One precedence, written once, is what keeps that true —
`api-design.md` § "Domain rules live with the domain; the renderer lays out what
it is handed" is why it is here rather than in each client.
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


def derive_item_status(archived: bool, completed: bool) -> str:
    """Name the status of one item, applying the same precedence as the filter.

    `archived` beats `completed`, so an item that was finished and then archived
    answers to `archived` alone and every item answers to exactly one word.
    """
    if archived:
        return 'archived'
    if completed:
        return 'completed'
    return 'open'


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
