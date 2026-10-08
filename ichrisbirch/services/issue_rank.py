"""Place issues in the one global order that breaks ties inside a priority.

`rank` is a float, the way Linear's `sortOrder` is. A new issue goes one past
the last. A move takes the midpoint of its two new neighbors, so it writes one
row. Halving a gap runs out of precision eventually, so when the gap left
between two neighbors falls below `MIN_GAP`, every rank is renumbered to whole
numbers in its current order and the midpoint is taken again.
"""

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.orm import Session

from ichrisbirch import models

# Far above the point where doubles stop distinguishing neighbors near the
# largest rank a table this size reaches, and far below any gap a renumber
# leaves, which is 1.
MIN_GAP = 1e-6


def rank_at_end(session: Session) -> float:
    highest = session.scalar(select(func.max(models.Issue.rank)))
    return (highest or 0.0) + 1.0


def renumber_ranks(session: Session) -> None:
    """Rewrite every rank as its position in the current order, starting at 1.

    Pending changes are flushed first, because the rows are expired afterwards
    so every loaded issue reads its new rank.
    """
    session.flush()
    position = func.row_number().over(order_by=(models.Issue.rank, models.Issue.created_ts, models.Issue.id)).label('position')
    ordered = select(models.Issue.id, position).subquery()
    session.execute(
        update(models.Issue).where(models.Issue.id == ordered.c.id).values(rank=ordered.c.position),
        execution_options={'synchronize_session': False},
    )
    session.expire_all()


def _neighbor_before(session: Session, issue: models.Issue, anchor: models.Issue) -> float | None:
    """The rank of whatever sits directly before `anchor`, other than `issue` itself."""
    return session.scalar(
        select(models.Issue.rank)
        .where(models.Issue.rank < anchor.rank, models.Issue.id != issue.id)
        .order_by(models.Issue.rank.desc())
        .limit(1)
    )


def _neighbor_after(session: Session, issue: models.Issue, anchor: models.Issue) -> float | None:
    return session.scalar(
        select(models.Issue.rank)
        .where(models.Issue.rank > anchor.rank, models.Issue.id != issue.id)
        .order_by(models.Issue.rank.asc())
        .limit(1)
    )


def _between(low: float | None, high: float | None) -> float | None:
    """The midpoint, or one step past an open end. None when the gap is spent."""
    if low is not None and high is not None:
        return (low + high) / 2 if high - low >= MIN_GAP else None
    if low is not None:
        return low + 1.0
    if high is not None:
        return high - 1.0
    return 1.0


def _rank_beside(session: Session, issue: models.Issue, before: models.Issue | None, after: models.Issue | None) -> float | None:
    if before is not None:
        return _between(_neighbor_before(session, issue, before), before.rank)
    if after is not None:
        return _between(after.rank, _neighbor_after(session, issue, after))
    raise ValueError('a move needs a neighbor: before or after')


def move_issue(session: Session, issue: models.Issue, *, before: models.Issue | None = None, after: models.Issue | None = None) -> None:
    """Rank `issue` immediately before `before`, or immediately after `after`."""
    rank = _rank_beside(session, issue, before, after)
    if rank is None:
        renumber_ranks(session)
        rank = _rank_beside(session, issue, before, after)
    if rank is None:
        raise RuntimeError('rank gap still spent after renumbering')
    issue.rank = rank
