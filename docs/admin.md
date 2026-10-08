# Admin Dashboard

The admin area is the Vue app's `/admin` pages, and only an admin user reaches them.
The Vue router checks the `requiresAdmin` route meta, which spares a non-admin a page of errors.
The API is what enforces it.
Every route on the admin router sits behind a router-level `get_admin_user` dependency in `ichrisbirch/api/main.py`.

## System

`/admin` shows the server, the `icb-` containers, Postgres, Redis and the disk.
Beside them it lists the API's recent 4xx and 5xx responses.
With auto-refresh on, the page rereads both every 30 seconds.

The recent errors come from a ring buffer in `ichrisbirch/api/middleware.py`.
It holds the last 200 per API process and empties when the process restarts.

The deploy color is read from `/var/lib/ichrisbirch/bluegreen-state`.
Outside production that file is absent, so no color is shown.

### A slow dependency reads as unavailable, and holds no other request

The health read is a `def` handler, so FastAPI runs it in its threadpool.
Every probe in it is blocking I/O.
On the event loop, one slow probe would hold every other request the worker is serving.

`PROBE_TIMEOUT_SECONDS` in `ichrisbirch/api/endpoints/admin.py` bounds each call a probe makes:

- **Docker** uses the client's API timeout. An unreachable daemon reads as "Docker status unavailable".
- **Postgres** sets a `statement_timeout` local to the probe's transaction. A cancelled query reads as empty stats instead of failing the whole read.
- **Redis** gets its own client with a connect and read timeout and one immediate retry. A refused or silent server reads as `N/A`. redis-py's own default sets no timeout and retries with exponential backoff, which turns a refused AUTH into many seconds of waiting.

The API mounts the Docker socket to read container status.
CI's compose file drops that mount, so the Docker section always reads as unavailable there.

## Scheduler

`/admin/scheduler` lists the APScheduler jobs in the jobstore with their next run.
Each can be paused, resumed or deleted.
The page also shows the run history the scheduler records in the database.

## Users

`/admin/users` lists every user account.

## Config

`/admin/config` shows every settings section.
A value is masked when its field name contains `key`, `secret`, `password` or `token`.
Masking goes by the name alone, so a secret stored under any other name is shown.

## Smoke Tests

`/admin/smoke` calls every GET route in the API's own route table and reports each status.
It runs in-process through `httpx2.ASGITransport`, as the requesting admin.
A route with a path parameter or a required query parameter is skipped, because there is no value to call it with.

## Design

`/admin/design` previews the color themes against the shadow styles and the segmented toggle experiments.
It is a workbench for the design-style switcher rather than an admin function.

## Log Stream

The API also serves a `/admin/log-stream/` WebSocket that tails every `*.log` file in `LOG_DIR`.
It authenticates with a `ws_auth` cookie holding an HMAC token signed with `internal_service_key`.
No current client issues that cookie or opens the socket.
Service logs are read in Loki, as [Logging Configuration](logging-configuration.md) describes.
