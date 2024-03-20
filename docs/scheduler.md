# Scheduler

## APScheduler

The scheduler is run in it's own `wsgi` application managed by `supervisor`.
The scheduler is using the standard blocking scheduler since it is in its own process.
Workers need to be set to 1 for `gunicorn` in order to not start multiple instances of the scheduler.
Technically the scheduler could be run as part of the API since the tasks are related to the API, but the API will be changing to async in the future which would require a different scheduler, and the jobs may not always be only related to the API.

The jobs are located in the `jobs.py` file in the `/scheduler` directory.

## Current Jobs

`decrease_task_priority` - Decreases the priority of all tasks by 1 every 24 hours.

`check_and_run_autotasks` - Checks if any autotasks need to be run based on their schedule and runs them if so.

`backup_database` - Backs up the postgres database to S3 every 3 days.
