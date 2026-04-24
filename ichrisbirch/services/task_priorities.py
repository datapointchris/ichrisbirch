"""Task priority compaction service.

Dense-ranks incomplete tasks to contiguous priorities 1..K, breaking ties by
`add_date ASC` (oldest-waiting surfaces first). Used by the nightly
scheduler job and by the on-demand `/reorder` API endpoint.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ichrisbirch import models


def compact_incomplete_task_priorities(session: Session) -> int:
    """Dense-rank incomplete tasks to priorities 1..K by (priority, add_date).

    Returns the number of tasks that were compacted. Does not commit — the
    caller owns the transaction boundary.
    """
    query = select(models.Task).filter(models.Task.complete_date.is_(None)).order_by(models.Task.priority.asc(), models.Task.add_date.asc())
    tasks = list(session.scalars(query).all())
    for new_rank, task in enumerate(tasks, start=1):
        task.priority = new_rank
    return len(tasks)
