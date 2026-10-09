# Admin Dashboard

The admin area is the Vue app's `/admin` pages, and only an admin user reaches them.
The Vue router checks the `requiresAdmin` route meta, which spares a non-admin a page of errors.
The API enforces it with a router-level `get_admin_user` dependency on the admin router, in `ichrisbirch/api/main.py`.

## System

`/admin` shows the server, the `icb-` containers, Postgres, Redis and the disk.
Beside them it lists the API's recent 4xx and 5xx responses.
With auto-refresh on, the page rereads both on a timer.

The recent errors come from the `recent_errors` ring buffer in `ichrisbirch/api/middleware.py`.
Each API process keeps its own, up to the buffer's `maxlen`, and it empties when the process restarts.

The deploy color is read from `/var/lib/ichrisbirch/bluegreen-state`.
Outside production that file is absent, so no color is shown.

### A slow dependency reads as unavailable, and holds no other request

The health read is a `def` handler, so FastAPI runs it in its threadpool.
Every probe in it is blocking I/O.
On the event loop, one slow probe would hold every other request the worker is serving.

A probe that gets no answer puts `null` in its section of the response, and the page shows that section as unavailable.
Zeros would read as a measured, idle dependency.
`PROBE_TIMEOUT_SECONDS` in `ichrisbirch/api/endpoints/admin.py` sets every bound:

- **Docker** makes several API calls per container. Each call has the client's API timeout, and the whole probe runs on one worker thread under the same deadline.
- **Postgres** sets a `statement_timeout` local to the probe's transaction, so each of its queries is cancelled at the bound.
- **Redis** gets its own client with a connect and read timeout. It retries a dropped connection once and never a command that timed out, because that command may already have run. redis-py's own default sets no timeout and retries connection errors and timeouts alike with exponential backoff. Under that default a refused AUTH takes around 11 s to fail.

The API mounts the Docker socket to read container status.
CI's compose file drops that mount, so the Docker section always reads as unavailable there.

## Scheduler

`/admin/scheduler` lists the APScheduler jobs in the jobstore with their next run.
Each can be paused, resumed or deleted.
The page also shows the run history the scheduler records in the database.

## Users

`/admin/users` lists every user account, and grants or revokes admin through `PATCH /users/{id}/`.
That route answers 403 to `is_admin` from anyone but an admin or the internal service, so a user cannot promote themselves.

Above the list, the Signups toggle decides who may create an account through `POST /users/`.
While closed, only an admin may, and every other caller gets 400 with `Refusal.SIGNUPS_CLOSED`.
While open, anyone may, including a caller with no login.
No model is scoped per user, so an account created while open can read and write every row.

The toggle writes `is_signup_open` in `admin.settings` through `PATCH /admin/settings/`.
That table is one row of settings an admin changes without a redeploy.
`POST /users/` reads the row on every request, so the next signup sees the change.
The migration that creates the row seeds it closed.
`full_initialization` seeds it again when the table is empty, as `create_all` and the test suite's truncate leave it.

## Config

`/admin/config` shows every section of the environment's configuration, which the containers read at startup.
It is read-only, unlike `admin.settings`.
A value is masked when its field name contains `key`, `secret`, `password` or `token`.
Masking goes by the name alone, so a secret stored under any other name is shown.

## Smoke Tests

`/admin/smoke` calls the GET routes that `discover_get_endpoints` in `ichrisbirch/api/smoke_tests.py` selects, and reports each status.
It runs in-process through `httpx2.ASGITransport`, as the requesting admin.
A route with a path parameter or a required query parameter is skipped, because there is no value to call it with.
The `/auth/` routes and the route names in `SKIP_NAMES` are skipped too.
A green report says nothing about a skipped route.

## Design

`/admin/design` previews the color themes against the shadow styles and the segmented toggle experiments.
It is a workbench for the design-style switcher rather than an admin function.

## Logs

The admin area has no log viewer.
Service logs are read in Loki, or from a terminal with `./ops/icbops {dev,testing,prod} logs [service]`.
[Logging Configuration](logging-configuration.md) covers both.
