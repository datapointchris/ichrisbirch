"""Which issues can be taken now, and in what order.

Readiness is derived on every read and never stored, because every input to it
changes elsewhere: a blocker closing, a claim expiring, a deferral day arriving,
a child closing. A stored flag would be wrong the moment any of them moved.

An issue is ready when all of these hold:

- it is `open`, or `in_progress` under a claim that has expired
- its deferral day, if any, has arrived in the reader's calendar
- every issue it depends on is closed
- it has no open children, since a parent is finished by its children

Order is effective priority, then rank, then number. An issue's own priority wins.
With none, it takes its open parent's effective priority, else its active
initiative's. Then it is raised to the most urgent effective priority of any
open issue it blocks. That last step is priority inheritance from scheduling:
without it a blocker ranked near the bottom keeps waiting while the work it
gates sits at the top of the queue, hidden because it is blocked.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch.models.issue import CLOSED_ISSUE_STATUSES

# The urgency of "no priority": after every real level, which run 1 (urgent)
# to 4 (low).
NO_PRIORITY_URGENCY = 5


def urgency(priority: int) -> int:
    return priority or NO_PRIORITY_URGENCY


def priority_of(urgency_value: int) -> int:
    return 0 if urgency_value == NO_PRIORITY_URGENCY else urgency_value


@dataclass(frozen=True)
class IssueReadiness:
    effective_priority: dict[UUID, int]
    blocked: frozenset[UUID]
    deferred: frozenset[UUID]
    ready: frozenset[UUID]
    child_count: dict[UUID, int]
    open_child_count: dict[UUID, int]

    def sort_key(self, issue: models.Issue) -> tuple[int, float, int]:
        """Number breaks a rank tie because it is issued in creation order and never repeats."""
        return (urgency(self.effective_priority.get(issue.id, issue.priority)), issue.rank, issue.number)


def measure_readiness(session: Session, today: date, now: datetime) -> IssueReadiness:
    """Read every issue's light columns once and derive the readiness of all of them.

    One pass over the whole table is cheaper than asking per issue, and the
    inheritance walks the graph anyway, so no subset of rows would be enough.
    """
    columns = (
        models.Issue.id,
        models.Issue.status,
        models.Issue.priority,
        models.Issue.initiative_id,
        models.Issue.parent_id,
        models.Issue.deferred_until_date,
        models.Issue.claim_expires_ts,
    )
    rows = {row.id: row for row in session.execute(select(*columns)).all()}
    initiative_urgency = {
        row.id: urgency(row.priority)
        for row in session.execute(
            select(models.Initiative.id, models.Initiative.priority).where(models.Initiative.status == 'active')
        ).all()
    }
    edges = session.execute(select(models.IssueDependency.issue_id, models.IssueDependency.depends_on_id)).all()

    unclosed = {issue_id for issue_id, row in rows.items() if row.status not in CLOSED_ISSUE_STATUSES}

    dependents: dict[UUID, list[UUID]] = {}
    blocked: set[UUID] = set()
    for issue_id, depends_on_id in edges:
        dependents.setdefault(depends_on_id, []).append(issue_id)
        if issue_id in unclosed and depends_on_id in unclosed:
            blocked.add(issue_id)

    child_count: dict[UUID, int] = {}
    open_child_count: dict[UUID, int] = {}
    for issue_id, row in rows.items():
        if row.parent_id is not None:
            child_count[row.parent_id] = child_count.get(row.parent_id, 0) + 1
            if issue_id in unclosed:
                open_child_count[row.parent_id] = open_child_count.get(row.parent_id, 0) + 1

    memo: dict[UUID, int] = {}
    walking: set[UUID] = set()

    def effective_urgency(issue_id: UUID) -> int:
        if issue_id in memo:
            return memo[issue_id]
        # Every loop through a dependency or a parent edge is refused on write, so
        # re-entering means a row written around that check. Contributing nothing
        # keeps the walk finite.
        if issue_id in walking:
            return NO_PRIORITY_URGENCY
        walking.add(issue_id)
        row = rows[issue_id]
        if row.priority:
            best = row.priority
        elif row.parent_id in unclosed:
            best = effective_urgency(row.parent_id)
        else:
            best = initiative_urgency.get(row.initiative_id, NO_PRIORITY_URGENCY)
        for dependent_id in dependents.get(issue_id, []):
            if dependent_id in unclosed:
                best = min(best, effective_urgency(dependent_id))
        walking.discard(issue_id)
        memo[issue_id] = best
        return best

    effective_priority = {
        issue_id: priority_of(effective_urgency(issue_id)) if issue_id in unclosed else row.priority for issue_id, row in rows.items()
    }

    deferred = {
        issue_id for issue_id in unclosed if rows[issue_id].deferred_until_date is not None and rows[issue_id].deferred_until_date > today
    }

    ready = set()
    for issue_id in unclosed:
        row = rows[issue_id]
        takeable = row.status == 'open' or (
            row.status == 'in_progress' and row.claim_expires_ts is not None and row.claim_expires_ts <= now
        )
        if takeable and issue_id not in deferred and issue_id not in blocked and not open_child_count.get(issue_id):
            ready.add(issue_id)

    return IssueReadiness(
        effective_priority=effective_priority,
        blocked=frozenset(blocked),
        deferred=frozenset(deferred),
        ready=frozenset(ready),
        child_count=child_count,
        open_child_count=open_child_count,
    )
