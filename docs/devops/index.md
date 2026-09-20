# DevOps

## Documentation

- [New Server Setup](new_server.md) — apt packages, pyenv, supervisor and nginx on a fresh Ubuntu host
- [New Database](new_database.md) — creating the schemas by hand, then the first alembic autogenerate
- [pg_cron](pg_cron.md) — the Postgres job scheduler, kept for reference and replaced by APScheduler
- [NGINX](nginx.md) — the bare-metal reverse proxy and its port layout, replaced by Traefik
- [Supervisor](supervisor.md) — the bare-metal process manager and its worker counts, replaced by Docker

The last three describe how the app ran before it was containerized. Each says
what replaced it, because the config files are still in the tree and reading one
without that note leads to a deploy path that no longer exists.

## Scheduled work

Jobs are APScheduler entries in a Postgres jobstore, added at runtime rather
than declared in this repo, so the job list is read from the scheduler and not
from a file here. `ichrisbirch/scheduler/main.py` is where the store is
attached.

`icbops stats` is the project-statistics surface — `summary`, `code`, `tests`,
`quality`, `activity`, `events`, `trends`, `churn` and `snapshot`.

`scripts/bootstrap-homelab.sh` restores a database dump into
`icb-infra-postgres` with `pg_restore`.
