# Docker Compose Architecture

`docker-compose.yml` holds production defaults. Each environment layers a file
over it. Blue/green production is the exception and does not use the base at
all.

## What each environment composes

| Environment | Files                | Project name                          |
| ----------- | -------------------- | ------------------------------------- |
| Development | base + `dev`         | `icb-dev`                             |
| Testing     | base + `test`        | `icb-test-<checkout directory>`       |
| CI          | base + `test` + `ci` | `icb-test-ichrisbirch`                |
| Production  | `infra`, then `app`  | `icb-infra`, `icb-blue` / `icb-green` |

`ops/icbops` holds these combinations as `COMPOSE_DEV`, `COMPOSE_TEST`,
`COMPOSE_INFRA` and a `compose_app` function. Read them there rather than
assembling `-f` flags by hand.

The base file is also runnable on its own, as project `icb-prod`. That is the
single-color path blue/green replaced. `icbops prod start` falls back to it
only when `/var/lib/ichrisbirch/bluegreen-state` names no active color.
`prod rebuild` refuses to run it at all, because rebuilding in place means
downtime.

## Layering merges lists instead of replacing them

Compose merges later files over earlier ones, and a field's type decides how.

| Field                | How an override combines with the base |
| -------------------- | -------------------------------------- |
| `ports`              | Appended                               |
| `volumes`            | Appended                               |
| `environment`        | Merged per key                         |
| `labels`             | Merged per key                         |
| `command`            | Replaced whole                         |
| `entrypoint`         | Replaced whole                         |
| `healthcheck.test`   | Replaced whole                         |

A dev override adding a port leaves the base's mapping in place and both bind.
That reads as `port already allocated` on a stack that looks correctly
configured.

`!override` replaces an appended list instead:

```yaml
services:
  api:
    volumes: !override
      - .:/app
      - /app/.venv
```

An `!override` list is a complete list, so anything the base contributed has to
be written out again. That is why `docker-compose.ci.yml` repeats `.:/app` and
`/app/.venv` while dropping only the Docker socket.

So `!override` belongs on `ports` and `volumes` and nowhere else. Putting it on
`environment` replaces the whole block, and every variable the base set and the
override did not name is gone. Those merge per key already, so there was
nothing to suppress.

`icbops {dev,testing,prod} docker [service]` prints the resolved result.
Read that rather than reasoning from the override file, because a field the
base already set looks like the override's doing.

## Services

| Service     | Internal port       | Notes                                 |
| ----------- | ------------------- | ------------------------------------- |
| `traefik`   | 80, 443, 8080       | Reverse proxy, TLS, dashboard on 8080 |
| `postgres`  | 5432                | PostgreSQL 16                         |
| `redis`     | 6379                | Redis 7                               |
| `api`       | 8000                | FastAPI                               |
| `vue`       | 5173, or 80 in prod | Vite dev server, or Caddy             |
| `scheduler` | none                | APScheduler, no listening socket      |

`api` and `scheduler` wait on health checks rather than start order:

```yaml
depends_on:
  postgres:
    condition: service_healthy
  redis:
    condition: service_healthy
```

### Routing comes from the file provider

Traefik's routers and middlewares are files, at
`deploy-containers/traefik/dynamic/{env}/routing.yml`. Compose labels declare
only the service ports Traefik forwards to. Vue path prefixes are generated
into those routing files from `deploy-containers/traefik/vue-paths.txt` by
`icbops routing generate`, so a new Vue route needs an entry there or Traefik
sends the path to the API.

## Development

Dev mounts `.:/app`, so the API reloads on save. `uvicorn` runs with `--reload`
scoped to `ichrisbirch/api`, `ichrisbirch/models` and `ichrisbirch/schemas` —
an edit outside those directories needs a restart.

### The Vue mount overlaps a bind mount with a named volume

```yaml
volumes:
  - ./frontend:/app
  - vue_node_modules:/app/node_modules
```

The bind mount alone would expose the host's `node_modules/` to the container,
which is either empty or built for the host's platform. The named volume
shadows that one subpath, so packages installed in the container land in
Docker-managed storage.

Docker needs `./frontend/node_modules/` to exist on the host as a mount point.
Where it does not, the daemon creates it, and the daemon runs as root. The
directory ends up owned by `root:root`:

- The host directory looks empty even after `npm install` ran in the container.
- A host-side `npm install` writes into a root-owned directory and fails with
  `EACCES`. Create it as yourself first with `mkdir frontend/node_modules` if
  you need host-side packages, for a pre-commit typecheck.
- No compose setting changes this. It is mount semantics, not configuration.

A partial install left in the named volume produces `ENOTEMPTY` in a restart
loop, and a loop left running long enough has taken down `dockerd` itself.
`icbops testing rebuild --all --volumes` wipes the volume and starts clean.
[Docker troubleshooting](../troubleshooting/docker-issues.md#container-crash-loop-that-crashes-dockerd)
has the recovery for a daemon that has already crashed.

## Testing

Every checkout gets its own test stack, and the e2e suite runs inside it.
pytest uses none of it: each session starts its own Postgres and Redis.

`ops/icbops` passes `--project-name icb-test-<checkout directory>`, and
`docker-compose.test.yml` scopes everything else to that name:

- **Container names** are `${COMPOSE_PROJECT_NAME}-<service>`.
- **Volumes and networks** carry no `name:`, so compose prefixes them with the
  project.
- **No port is published.** Every service sets `ports: !override []`, so any
  number of stacks and the dev stack run side by side.
- **Traefik reads only files.** `deploy-containers/traefik/dynamic/test/services.yml`
  routes to `http://api:8000` and `http://vue:5173`, which resolve on the
  project's own network. A Docker provider would see every stack on the daemon
  and merge their `api` services into one load balancer.
- **Vue runs Playwright's image**, which carries Node and Chromium, so the dev
  server and the e2e suite share one container.

Its Postgres keeps data on tmpfs and runs with `fsync`, `synchronous_commit`
and `full_page_writes` off. Tests do not need durability. Dropping it is most
of the speed difference.

The database therefore empties whenever that container stops or is recreated.
Every `icbops` verb that brings the stack up initializes it afterwards. A bare
`docker compose up` does not, which leaves an empty database behind healthy
containers:

```bash
./ops/icbops test e2e          # starts the stack if needed, then runs Playwright in it
./ops/icbops testing start     # leaves it up for repeated runs
```

[Test Environment Configuration](../testing/environment.md) covers both suites.

## CI

CI layers a third file over base and test. `icbops` adds it when `CI=true`,
which GitHub sets on every job. The e2e job runs `./ops/icbops testing start`
and `./ops/icbops test e2e`, the same commands a workstation runs, so the
project is `icb-test-ichrisbirch`, after the runner's checkout directory.

The file changes one thing. **The API's Docker socket is dropped.** The API
mounts it to report container status on the admin dashboard, through
`get_docker_containers()` in `ichrisbirch/api/endpoints/admin.py`. A runner
has no reason to hand that in.

Do not add a named volume for `.venv` or the uv cache to any of these files.
Named volumes survive rebuilds, so a stale virtualenv outlives the image meant
to replace it, and the API hangs in `health: starting` while `uv` resyncs. The
anonymous `/app/.venv` volume is what keeps dev, test and CI behaving alike.

## Production

`docker-compose.infra.yml` runs Traefik, Postgres and Redis as project
`icb-infra`, and stays up across deploys. `docker-compose.app.yml` runs the API,
Vue and scheduler as `icb-blue` or `icb-green`.

Neither builds anything. Both name images from
`ghcr.io/datapointchris/`, which `.github/workflows/release.yml` pushes. The
deploy pulls the tag and starts containers.

`DEPLOY_COLOR` is the only variable distinguishing the two app projects, and
`scripts/deploy-homelab.sh` sets it per invocation. [Blue/green
deployment](../blue-green-deployment.md) covers the sequence.

## When a change is not taking effect

Containers hold stale state in ways that look like application bugs: a route
returning 404 after it was added, an import failing for a package that is in
`pyproject.toml`. Work the escalation ladder in
[Testing troubleshooting](../troubleshooting/testing-issues.md#a-change-is-not-taking-effect)
before reading any of this page's diagnostics.

## Related

- [Docker Architecture and Build Process](docker.md)
- [Quick Reference](docker-quick-reference.md)
- [Docker troubleshooting](../troubleshooting/docker-issues.md)
