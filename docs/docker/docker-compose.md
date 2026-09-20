# Docker Compose Architecture

`docker-compose.yml` holds production defaults, and each environment layers a
file over it. Blue/green production is the exception and does not use the base
at all.

## What each environment composes

| Environment | Files                | Project name                          |
| ----------- | -------------------- | ------------------------------------- |
| Development | base + `dev`         | `icb-dev`                             |
| Testing     | base + `test`        | `icb-test`                            |
| CI          | base + `test` + `ci` | `icb-test`                            |
| Production  | `infra`, then `app`  | `icb-infra`, `icb-blue` / `icb-green` |

`ops/icbops` holds these combinations as `COMPOSE_DEV`, `COMPOSE_TEST`,
`COMPOSE_INFRA` and a `compose_app` function. Read them there rather than
assembling `-f` flags by hand — `icbops {dev,testing,prod} docker config` prints
the merged result for any of them.

The base file is also runnable on its own, as project `icb-prod`. That is the
single-color path blue/green replaced. `icbops prod start` falls back to it only
when `/var/lib/ichrisbirch/bluegreen-state` names no active color, and
`prod rebuild` refuses to run it because rebuilding in place means downtime.

## Layering merges lists instead of replacing them

Compose merges later files over earlier ones, but list-valued keys —
`ports`, `volumes`, `environment`, `labels`, `command` — append rather than
replace. So a dev override adding a port leaves the base's port mapping in
place, and both bind. The symptom is `port already allocated` on a stack that
looks correctly configured.

`!override` replaces the list instead:

```yaml
services:
  api:
    volumes: !override
      - .:/app
      - /app/.venv
```

Every list an environment file redefines carries it. An `!override` list is a
complete list, so anything the base contributed has to be written out again —
that is why `docker-compose.ci.yml` repeats `/app/.venv` and the logs volume
while dropping only the Docker socket.

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
Where it does not, the daemon creates it, and the daemon runs as root — so the
directory ends up `root:root`. Three consequences follow:

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

The test stack runs alongside dev on other ports, so both can be up at once.

| Service       | Dev  | Test |
| ------------- | ---- | ---- |
| API           | 8000 | 8001 |
| Vue           | 5173 | 5174 |
| PostgreSQL    | 5432 | 5434 |
| Redis         | 6379 | 6380 |
| Traefik HTTPS | 443  | 8443 |
| Traefik HTTP  | 80   | 9080 |

Its Postgres keeps data on tmpfs and runs with `fsync`, `synchronous_commit`
and `full_page_writes` off. Durability is what tests do not need, and dropping
it is most of the speed difference.

The database therefore empties whenever that container stops or is recreated.
Every `icbops` verb that brings the stack up initializes it afterwards, and
pytest's session setup migrates it to head. A bare `docker compose up` does
neither, which leaves an empty database behind healthy containers:

```bash
./ops/icbops test run          # starts the stack if needed, then runs pytest
./ops/icbops testing start     # leaves it up for repeated runs
```

[Test Environment Configuration](../testing/environment.md) covers what a
pytest session does against the stack.

## CI

CI layers a third file over base and test, because a GitHub runner differs from
a workstation in four ways.

| Difference        | Local                        | CI                         |
| ----------------- | ---------------------------- | -------------------------- |
| Docker socket     | Mounted in for the prune job | Dropped                    |
| Proxy network     | Created externally           | Created as internal bridge |
| Vue image         | `node:24-alpine`             | `build` reset to null      |
| Traefik dashboard | Useful for debugging         | Disabled                   |

So `docker-compose.ci.yml` drops the socket with an `!override` volume list and
declares the proxy network as an internal bridge.

Resetting `build` on `vue` to null is the one that is not obvious. CI brings
the stack up with `--build`, and the test override's `vue` is a plain
`node:24-alpine` with a `build` section inherited from the base. Without the
reset, `--build` would build `frontend/Dockerfile` and replace the dev server
with the production Caddy image. That health check's `start_period` is extended
too, because `npm install` runs from scratch on a fresh volume.

Do not add a named volume for `.venv` or the uv cache to any of these files.
Named volumes survive rebuilds, so a stale virtualenv outlives the image meant
to replace it, and the API hangs in `health: starting` while `uv` resyncs. The
anonymous `/app/.venv` volume is what keeps dev, test and CI behaving alike.

`.github/workflows/validate.yml` starts `postgres` and `redis`, then `api` and
`scheduler`, each with `--wait` so the next service starts against a healthy
dependency. A separate step migrates the database before pytest or Playwright
runs.

The fixtures detect CI and skip container management, because the workflow has
already done it:

```python
@property
def is_ci(self) -> bool:
    return os.environ.get('CI', '').lower() == 'true'
```

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

Containers hold stale state in ways that look like application bugs — a route
returning 404 after it was added, an import failing for a package that is in
`pyproject.toml`. Work the ladder in order.

1. `./ops/icbops testing stop && ./ops/icbops testing start`. Around 30
   seconds. This clears accumulated database state, unregistered routes and
   stale module imports.
2. `./ops/icbops testing rebuild --volumes`. Around 60 to 90 seconds. This
   clears stale `.venv` contents, dependency changes, anonymous-volume
   staleness and a corrupted `node_modules`.
3. Only now, `docker logs`, `docker inspect`, `docker exec`.

The same ladder applies to dev through `icbops dev`.

Reaching for a manual `docker` subcommand before steps 1 and 2 is the single
largest time sink in this workflow. A container that has not been through them
is not evidence of anything. The tell that it has gone wrong is proposing a
workaround rather than an escalation — baking the virtualenv into the image is
a workaround, and step 2 is the escalation.

## Related

- [Docker Architecture and Build Process](docker.md)
- [Quick Reference](docker-quick-reference.md)
- [Docker troubleshooting](../troubleshooting/docker-issues.md)
