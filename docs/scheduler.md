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
| `make_logs` | every 15 seconds | Heartbeat / log sanity check |
| `check_and_run_autotasks` | daily at 1:00 AM | Create new Tasks from AutoTask templates whose schedule fires today and are under `max_concurrent` |
| `check_and_run_autofun` | daily at 1:00 AM | Sync AutoFun active tasks and fill open slots from the fun list |
| `compact_task_priorities` | daily at 1:15 AM | Dense-rank all incomplete Task priorities to `1..K` (tiebreak by `add_date ASC`) — runs *after* autotasks so same-night seeded tasks get included |
| `docker_prune` | weekly, Sunday 3:00 AM | Prune Docker images older than 7 days to free disk space |

Task priority is a positional rank, not a time budget — `compact_task_priorities` is
cosmetic housekeeping, not correctness-critical. The `/tasks/reorder/` API
endpoint runs the same logic on demand.
