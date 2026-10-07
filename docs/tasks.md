# Tasks

A task is something to do on a cadence, not an appointment. Appointments
belong to events. So the task list never shows a due date or an overdue count,
even though it is sorted by one.

## The list is sorted by when each task should reach the top

Open tasks read in this order:

```sql
ORDER BY pinned DESC, rank_at ASC, add_date ASC
```

`rank_at` is the moment a task should reach the top of the list. A new task
gets its creation time plus its window, in `window_days`. The window comes
from the request when one is given, and from the task's category otherwise.

| Category | Window (days) |
| --- | --- |
| Dingo | 7 |
| Chore, Financial, Kitchen, Purchase | 30 |
| Automotive | 45 |
| Home, Personal, Work | 60 |
| Computer | 90 |
| Learn, Research | 180 |

Those are the defaults `TASK_CATEGORY_WINDOW_DAYS` seeds. The deployed values
live in `task_categories.window_days` and change through
`PATCH /tasks/categories/{name}/`. A changed window applies to the next task
in that category. Tasks already open keep the window they were made with.

The window is how fast a kind of task climbs. A nail trim with a 7-day window
passes a research interest added two months earlier, and the research task
still reaches the top once its 180 days run out. Both sit on one scale, so
they compare without a second "importance" field. Something more important is
something that should be done sooner, which a shorter window already says.

## A positional rank made the list a stack

The list used to sort by `priority`, a rank where 1 was the top. A new task
defaulted to 1, and a nightly job dense-ranked every open task to 1..K. That
turned each tie into a strict order. So every new task pushed every older one
down a place for good, and nothing moved a task back up.

```text
day 0   [A1 B2 C3]          add D at priority 1
night   [A1 D2 B3 C4]       compaction: D is now strictly ahead of B, C
day 1   add E at 1  ->  [A1 E2 D3 B4 C5]
```

Tasks finished within a week of arriving, and anything older sank below the
point the list was read to. `rank_at` cannot do that. A task's place depends
on its own date, which no other task's arrival changes.

`tasks.priority` keeps the rank each row had, and nothing writes it.

## Moving a task

| Action | What it writes |
| --- | --- |
| Snooze | `rank_at` = now + `window_days`, and unpins. The task goes back to the start of its window. |
| Pin | `pinned` = true. Pinned tasks sort ahead of every other. |
| Drag | a `rank_at` between the two neighbors it lands between |
| Drop | `drop_date` and an optional `drop_reason` |

`rank_at` is a timestamp rather than a day, so there is always a moment
between two neighbors to drag into.

A dropped task is one let go of. It stays on record, leaves the open list, and
does not count as completed. A task is open, completed or dropped, and the
`ck_tasks_one_closed_state` constraint keeps it from being both closed states.
Clearing `drop_date` reopens it.

## Autotasks add their copies through the same window

An autotask copy is created on the day it is due. Its window is the template's
`window_days`, or its category's when the template sets none. The copy records
its template in `tasks.autotask_id`.

Most templates are `completion` anchored. The next copy counts from when the
last one was completed or dropped, and only one copy is open at a time.
`docs/scheduler.md` describes both anchors.

## Rejected designs

*Rejected:* priority buckets such as now, soon and someday, first in first out
within each. A bucket stops a newer task passing an older one of the same
importance. But it gives up drag, and it has no way to let a slow task climb
past a fast one.

*Rejected:* aging computed at read time, `priority - days_waiting / N`. The
order shown would drift away from the order dragged, and N would need tuning.

*Rejected:* a fixed slot for the oldest task. It surfaces one old task at a
time and leaves the sort that buried it in place.
