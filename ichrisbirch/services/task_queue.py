"""Where a task sits in the open list.

Open tasks read in `(pinned DESC, rank_at ASC, add_date ASC)` order. A task's
`rank_at` is when it should reach the top: creation or the last snooze plus its
window, or wherever a drag put it. The API, the autotask run endpoint and the
scheduler's autotask and autofun jobs all make tasks through `new_task`, so the
window falls back to the category's the same way in each.
"""

from datetime import UTC
from datetime import datetime
from datetime import timedelta

from sqlalchemy import Select
from sqlalchemy.orm import Session

from ichrisbirch import models


def category_window_days(session: Session, category: str) -> int:
    """The category's window, or a LookupError naming the unknown category."""
    if row := session.get(models.TaskCategory, category):
        return row.window_days
    raise LookupError(f'Unknown task category {category!r}')


def new_task(
    session: Session,
    *,
    name: str,
    category: str,
    notes: str | None = None,
    window_days: int | None = None,
    pinned: bool = False,
    autotask_id: int | None = None,
    now: datetime | None = None,
) -> models.Task:
    """A task ranked `window_days` from now, the category's window when unset. Not added to the session."""
    now = now or datetime.now(UTC)
    window = window_days or category_window_days(session, category)
    return models.Task(
        name=name,
        category=category,
        notes=notes,
        window_days=window,
        rank_at=now + timedelta(days=window),
        pinned=pinned,
        autotask_id=autotask_id,
        add_date=now,
    )


def restart_window(task: models.Task, *, now: datetime | None = None) -> None:
    """Restart the task's window from now and unpin it, since a pinned task sorts first whatever its date."""
    now = now or datetime.now(UTC)
    task.rank_at = now + timedelta(days=task.window_days)
    task.pinned = False


def is_closed(task: models.Task) -> bool:
    return task.complete_date is not None or task.drop_date is not None


def match_fields_to_state(task: models.Task) -> None:
    """Unpin a closed task and clear the reason of one that is not dropped, as the table's checks require."""
    if is_closed(task):
        task.pinned = False
    if task.drop_date is None:
        task.drop_reason = None


def is_open(query: Select) -> Select:
    return query.filter(models.Task.complete_date.is_(None), models.Task.drop_date.is_(None))


def in_queue_order(query: Select) -> Select:
    return query.order_by(models.Task.pinned.desc(), models.Task.rank_at.asc(), models.Task.add_date.asc())
