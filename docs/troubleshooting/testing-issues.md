# Testing Environment Troubleshooting

The test stack is containerized and ephemeral. Most failures that look like
test bugs are stale container state, and the ladder below clears them faster
than reading logs does.

## A change is not taking effect

Work these in order. Do not substitute manual `docker` subcommands.

1. **`./ops/icbops testing stop && ./ops/icbops testing start`** — around 30
   seconds. Clears accumulated database state, routes FastAPI has not
   re-registered, and stale module imports. A changed model needs this.
2. **`./ops/icbops testing rebuild --volumes`** — around 60 to 90 seconds.
   Clears a stale `.venv`, a dependency added to `pyproject.toml`,
   anonymous-volume staleness, and a corrupted `node_modules`.
3. **Only now** reach for `docker logs`, `docker inspect` or `docker exec`.

Containers that have not been through steps 1 and 2 are not evidence of
anything. A fresh container from step 2 still failing is a real bug.

A new migration is the exception and needs neither step. pytest's session setup
migrates the test database to head before its fixtures run.

## Read the output files instead of re-running

Every pytest run — from the CLI or from pre-commit — writes two files:

| File                                  | Contents                            |
| ------------------------------------- | ----------------------------------- |
| `/tmp/ichrisbirch-pytest-output.log`  | Terminal output                     |
| `/tmp/ichrisbirch-pytest-report.json` | A `tests` array, one entry per test |

Each JSON entry carries `nodeid`, `outcome` and `call.longrepr`. Reading these
beats re-running a long suite to capture different output.

## The test database

It lives on tmpfs, so every stop or recreate of the Postgres container empties
it. That is the design, not a fault.

Every `icbops` verb that brings the stack up initializes the database
afterwards — `testing start`, `testing restart`, `testing rebuild` with any
flags, and `test run`'s cold start. pytest then migrates it to head, and its
fixtures truncate between tests.

A bare `docker compose up` does none of that. It leaves an empty database
behind healthy containers, which surfaces as `relation "..." does not exist` on
the first query.

**Never repair it by hand.** No `psql`, no alembic stamp, no raw SQL. The fix
is `testing stop` then `testing start`. If that cannot recover it, that is a
CLI bug worth fixing rather than routing around.

`testing db reset` drops and recreates everything. It is for a schema that is
genuinely corrupt, or a migration edited after it was applied. Restart the
containers afterwards so the API's connection pool stops pointing at dropped
objects.

## The API is stuck in `health: starting`

The API container runs `uvicorn` directly rather than `uv run`, and `/app/.venv`
is an anonymous volume that Docker re-seeds from the image layer on every new
container.

A named volume for `.venv` or for the uv cache breaks both properties. The
stale virtualenv outlives the image meant to replace it, and `uv` resyncs at
runtime while the health check times out. Do not reintroduce one in the test,
dev or CI compose files.

Step 2 of the ladder is the fix when this happens anyway.

## A new npm package 500s on some pages

The test Vue container keeps `node_modules` in a named volume and runs
`npm install && npm run dev` at startup. A package added to `package.json`
while the container is running is not installed in that volume.

```bash
./ops/icbops testing stop && ./ops/icbops testing start
```

The symptom is specific: pages importing the new package return 500 while every
other page works.

## `ENOTEMPTY` in a restart loop

Partial install state in `icb-test-vue-node-modules` — an `npm install`
interrupted mid-run — produces `ENOTEMPTY: directory not empty` in a loop. Left
running long enough, that loop has taken down `dockerd` itself.

```bash
./ops/icbops testing rebuild --all --volumes
```

If the daemon has already crashed, [Docker
troubleshooting](docker-issues.md#container-crash-loop-that-crashes-dockerd)
has the manual recovery.

## Port conflicts with the dev stack

The two stacks are meant to run together, on different ports.

| Service       | Dev  | Test |
| ------------- | ---- | ---- |
| API           | 8000 | 8001 |
| Vue           | 5173 | 5174 |
| PostgreSQL    | 5432 | 5434 |
| Redis         | 6379 | 6380 |
| Traefik HTTPS | 443  | 8443 |

`port already allocated` on a stack that looks correct usually means a compose
list merged instead of replacing. Compose appends `ports`, `volumes` and
`environment` across files unless the override carries `!override`.

## E2E tests

They run against the test containers, never dev, and always through Traefik at
`app.docker.localhost`. Hitting `vue.docker.localhost` bypasses the proxy, which
is where CORS and the auth middleware live — a test that passes there can still
fail in a browser.

E2E is smoke-level by design. Each page keeps a CORS check, a page load, sidebar
navigation and one CRUD roundtrip. Interaction-heavy cases live in the component
tests under `frontend/src/views/__tests__/`, and every E2E file names its
counterpart in a comment.

Two conventions keep them from breaking on unrelated changes. Selectors are
`data-testid`, never CSS classes or DOM structure. Assertions check generic
keywords like `added` or `deleted`, never exact notification text.

## Markers

Two markers are declared, and neither runs by default:

```bash
uv run pytest -m seed          # seed system tests
uv run pytest -m integration   # tests requiring running services
```

## Coverage

Configured in `pyproject.toml` under `[tool.coverage.run]`: parallel, branch
coverage, sourced from `ichrisbirch` with `ichrisbirch/alembic` omitted.
Migrations are generated and exercised by running them, so measuring them
reports noise.

```bash
./ops/icbops test run --cov=ichrisbirch --cov-report=html
```

Parallel mode writes one data file per worker. A report showing almost nothing
usually means those files were never combined.

## CI differs in four ways

`docker-compose.ci.yml` layers over base and test.

| Difference        | Local                        | CI                         |
| ----------------- | ---------------------------- | -------------------------- |
| Docker socket     | Mounted in for the prune job | Dropped                    |
| Proxy network     | Created externally           | Created as internal bridge |
| Vue image         | `node:24-alpine`             | `build` reset to null      |
| Traefik dashboard | Enabled                      | Disabled                   |

The Vue row is the one that bites. CI brings the stack up with `--build`, and
without that reset the build would replace the dev server with the production
Caddy image.

The fixtures detect CI through the `CI` environment variable and skip container
management, because `.github/workflows/validate.yml` has already started them
with `--wait`.

A failure that reproduces locally but not in CI, or the reverse, is usually one
of those four rows.

## Related

- [Test Environment](../testing/environment.md)
- [Testing Configuration](../testing/test_configuration.md)
- [Docker Compose Architecture](../docker/docker-compose.md)
- [Docker troubleshooting](docker-issues.md)
