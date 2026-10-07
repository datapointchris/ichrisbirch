"""Where a task sits in the open list.

Open tasks read in `(pinned DESC, rank_at ASC, add_date ASC)` order. A task's
`rank_at` is when it should reach the top: creation, or the last snooze, plus
its window. Every path that makes a task goes through `new_task`, so the window
falls back the same way whether the API, an autotask or autofun made it.
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


def is_open(query: Select) -> Select:
    return query.filter(models.Task.complete_date.is_(None), models.Task.drop_date.is_(None))


def in_queue_order(query: Select) -> Select:
    return query.order_by(models.Task.pinned.desc(), models.Task.rank_at.asc(), models.Task.add_date.asc())
