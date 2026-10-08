# Scheduler

## APScheduler

The scheduler runs as its own Docker container (`icb-{env}-scheduler` for
dev/test, `icb-{blue,green}-scheduler` for production). It uses APScheduler's
blocking scheduler in a single process — a single instance is required to
avoid duplicate job runs.

Every job execution is persisted as a `SchedulerJobRun` record (job id,
`job_run_id` correlation token, started/finished timestamps, duration, success,
error details) via the `job_logger` decorator. The decorator binds the
`job_run_id` into structlog contextvars for the duration of the run, so every
log line emitted during the job is queryable in Loki by
`{job_run_id="..."}` and joins back to the DB row of the same id.
Exceptions inside a job are logged but swallowed so one failing job cannot
take down the whole scheduler.

Jobs are registered in `ichrisbirch/scheduler/jobs.py` via `get_jobs_to_add()`.

## Current Jobs

| Job | Trigger | Purpose |
| --- | --- | --- |
| `make_logs` | every minute, at :15 seconds; paused at startup | Heartbeat / log sanity check |
| `check_and_run_autotasks` | daily at 1:00 AM | Create a Task from each AutoTask template that is due today and under its open-copy limit |
| `check_and_run_autofun` | daily at 1:00 AM | Sync AutoFun active tasks and fill open slots from the fun list |
| `docker_prune` | weekly, Sunday 3:00 AM | Prune Docker images older than 7 days to free disk space |

## The scheduler keeps the admin's calendar

Every time in the table above is read in the admin user's `timezone`
preference. No task, autotask or habit row records which user it belongs to,
so the admin is the one user a job can ask. `admin_calendar_zone` in
`jobs.py` answers UTC while the admin has no preference, and while the
`users` table does not exist yet. The test scheduler starts that way,
before its database is initialized.

The triggers read the zone once at startup, and the autotask job reads it on
every run:

- **The triggers.** APScheduler fixes a trigger's zone when the trigger is
  built, so `create_scheduler` reads the zone once at startup. A preference
  changed in settings moves 1:00 AM at the next restart, which every deploy
  does.
- **The autotask day.** `check_and_run_autotasks` reads the zone on every
  run. An autotask's first and last runs are instants, and the zone turns
  each into a day on the admin's calendar.

## An autotask counts from its last copy's close or from its first run

Each template has an `anchor`, and the anchor decides the day its next copy is
due. Both count in calendar units, which needs a pendulum `Date`: a pendulum
month added to a stdlib `date` is 30 days.

| Anchor | Next copy is due | Open copies |
| --- | --- | --- |
| `completion` | one step after the later of the last copy's close and the last run | one at a time |
| `calendar` | on the first run's day plus whole steps | up to `max_concurrent` |

A `completion` template suits upkeep that grows from the last time it was
done. Nails trimmed four days late are next due two weeks after that trim,
not ten days later. Copies are found through `tasks.autotask_id`. The last run
counts as well as the last close, because a copy deleted while open never
closes. Without it the next night would make a new copy.

A `calendar` template keeps fixed dates. A monthly one first run on January 31
is due on February 28 and then on March 31, and one first run on the 15th
stays on the 15th. A run held back at `max_concurrent` does not move the ones
after it.

## The task list is ordered at read time

Open tasks read in `pinned DESC, rank_at ASC, add_date ASC` order. A task's
`rank_at` is its creation plus its window, and snooze and drag move it, so
the order is right at every read. The windows are described in
`docs/tasks.md`.
