# Scheduler

## APScheduler

The scheduler is run in the background when the app and api are started.
The jobs are located in the `jobs.py` file in the `/scheduler` directory.

## Current Jobs

`decrease_task_priority` - Decreases the priority of all tasks by 1 every 24 hours.

`check_and_run_autotasks` - Checks if any autotasks need to be run based on their schedule and runs them if so.

`backup_database` - Backs up the postgres database to S3 every 3 days.
