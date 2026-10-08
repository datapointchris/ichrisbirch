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

`icb tasks categories list` prints each category's window.
`TASK_CATEGORY_WINDOW_DAYS` holds the defaults a new database starts with.
The deployed values live in `task_categories.window_days` and change through
`PATCH /tasks/categories/{name}/`. A changed window applies to the next task
in that category. Tasks already open keep the window they were made with.

The window is how fast a kind of task climbs. A nail trim with a 7-day window
passes a research interest added two months earlier, and the research task
still reaches the top once its 180 days run out. Both sit on one scale, so
they compare without a second "importance" field. Something more important is
something that should be done sooner, which a shorter window already says.

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
does not count as completed. `PATCH /tasks/{id}/reopen/` puts a completed or
dropped task back on the list at the `rank_at` it had.

## The table enforces what each state allows

A task is open, completed or dropped. Three checks hold the fields to the
state, so neither a verb nor a raw `PATCH /tasks/{id}/` can break them.

| Check | Rule |
| --- | --- |
| `one_closed_state` | never both completed and dropped |
| `pinned_only_open` | only an open task is pinned |
| `drop_reason_needs_drop_date` | only a dropped task has a reason |

`match_fields_to_state` in `services/task_queue.py` clears what a state
forbids. Complete, drop, reopen and the generic update all call it. So
completing a pinned task unpins it, and clearing `drop_date` clears the
reason. An update that asks to pin a closed task, or to give an open one a
reason, answers 409.

## Autotasks add their copies through the same window

An autotask copy is created on the day it is due. Its window is the template's
`window_days`, or its category's when the template sets none. The copy records
its template in `tasks.autotask_id`.

Most templates are `completion` anchored. The next copy counts from when the
last one was completed or dropped, and only one copy is open at a time.
`docs/scheduler.md` describes both anchors.

## Rejected designs

*Rejected:* a positional rank that a new task joins at the top. Each arrival
pushes every open task down one place, and nothing moves a task back up.
`rank_at` depends only on the task's own date, which no other arrival changes.

```text
day 0   [A1 B2 C3]          add D at priority 1
night   [A1 D2 B3 C4]       compaction: D is now strictly ahead of B, C
day 1   add E at 1  ->  [A1 E2 D3 B4 C5]
```

`tasks.priority` is a positional rank that nothing reads or writes.

*Rejected:* priority buckets such as now, soon and someday, first in first out
within each. A bucket stops a newer task passing an older one of the same
importance. But it gives up drag, and it has no way to let a slow task climb
past a fast one.

*Rejected:* aging computed at read time, `priority - days_waiting / N`. The
order shown would drift away from the order dragged, and N would need tuning.

*Rejected:* a fixed slot for the oldest task. It surfaces one old task at a
time and leaves the sort that buried it in place.
