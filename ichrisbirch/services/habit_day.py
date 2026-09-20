"""One day's habits: which are still due, and which were done.

Every client reads the split from here rather than joining two collection reads
itself. A fallback key written once per client is a key each client can spell
differently, and one that does disagrees with the others without anything
failing.

A day is a calendar day in a named zone, never a UTC day. A completion recorded
at 21:00 in New York is 01:00 the next day in UTC, so a UTC window would report
it against tomorrow and leave the habit reading as due tonight.
"""

import datetime as dt
from zoneinfo import ZoneInfo

from ichrisbirch import models


def day_bounds(day: dt.date, zone: ZoneInfo) -> tuple[dt.datetime, dt.datetime]:
    """The instants a calendar day opens and closes in one zone.

    Half-open: the end is the start of the next day, so a completion at 23:59:59
    belongs to the day it happened on and none is counted twice.

    The end is built from the next calendar day rather than by adding 24 hours.
    A day the zone shifts its offset is 23 or 25 hours long, and a fixed duration
    lands an hour inside or past midnight on those two days a year.
    """
    start = dt.datetime.combine(day, dt.time.min, tzinfo=zone)
    end = dt.datetime.combine(day + dt.timedelta(days=1), dt.time.min, tzinfo=zone)
    return start, end


def habit_key(name: str, category_id: int) -> str:
    """What identifies a habit to a completion that carries no `habit_id`.

    The category is part of the key because a name alone is not unique: a `Read`
    under Health and a `Read` under Mind are two habits, and one completion of
    either would otherwise tick off both.
    """
    return f'{category_id}\x00{name}'


def still_due(current: list[models.Habit], completed: list[models.HabitCompleted]) -> list[models.Habit]:
    """The current habits with no completion among `completed`.

    A completion carrying `habit_id` is matched by it, so a habit renamed since
    does not read as due again. One carrying none falls back to name and
    category, which is all such a row has — that is every completion recorded
    before the column existed, and every one whose habit has been deleted.
    """
    done_ids = {c.habit_id for c in completed if c.habit_id is not None}
    done_keys = {habit_key(c.name, c.category_id) for c in completed if c.habit_id is None}
    return [h for h in current if h.id not in done_ids and habit_key(h.name, h.category_id) not in done_keys]


def placement(habit_id: int | None) -> tuple[int, int]:
    """Where a row sits on the board, by the id of the habit it stands for.

    An id never changes, so a habit holds its place all day and ticking one off
    shuffles nothing around it. A completion carrying no `habit_id` has no habit
    to place it by, so the first element sends it after every row that has one.
    """
    if habit_id is None:
        return (1, 0)
    return (0, habit_id)
