# Testing Environment Troubleshooting

pytest starts its own Postgres and Redis for every session and discards them
after, so it carries no state between runs. The e2e suite runs inside the
checkout's test stack, which does. Most e2e failures that look like test bugs
are stale container state. A stop-and-start clears most of them, and a
`rebuild --volumes` clears the rest. Both cost less than reading logs.

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

pytest needs neither step. It runs the API in-process from the checkout's code,
and migrates a database created for the session.

## Read the output files instead of re-running

Every run from the CLI or from pre-commit writes its output to `.test-reports/`
in the checkout:

| File                                      | Contents                            |
| ----------------------------------------- | ----------------------------------- |
| `.test-reports/pytest-output.log`         | pytest's terminal output            |
| `.test-reports/pytest-report.json`        | A `tests` array, one entry per test |
| `.test-reports/playwright-report.json`    | The e2e suite's JSON report         |

Each pytest entry carries `nodeid`, `outcome` and `call.longrepr`. Reading these
beats re-running a long suite to capture different output. Playwright's traces
and screenshots land in `frontend/test-results/`.

## The test stack's database

It lives on tmpfs, so every stop or recreate of the Postgres container empties
it. That is the design, not a fault. pytest never connects to it.

Every `icbops` verb that brings the stack up initializes the database
afterwards — `testing start`, `testing restart`, `testing rebuild` with any
flags, and `test e2e`'s cold start. Initializing migrates to head, so a new
migration reaches the e2e suite after step 1 of the ladder.

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
is an anonymous volume that Docker seeds from the image layer. Every `icbops`
`up` passes `--renew-anon-volumes`, because compose otherwise hands a recreated
container the volume of the one it replaces.

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

Partial install state in the checkout's `icb-test-<checkout>-vue-node-modules`
volume — an `npm install` interrupted mid-run — produces `ENOTEMPTY: directory
not empty` in a loop. Left running long enough, that loop has taken down
`dockerd` itself.

```bash
./ops/icbops testing rebuild --all --volumes
```

If the daemon has already crashed, [Docker
troubleshooting](docker-issues.md#container-crash-loop-that-crashes-dockerd)
has the manual recovery.

## `port already allocated` from the test stack

The test stack publishes no ports. Every service in `docker-compose.test.yml`
replaces the base file's `ports` with `ports: !override []`. Compose appends
`ports` and `volumes` across files unless the override carries `!override`, so
a test service missing it publishes the dev port and collides with the dev
stack. `icbops testing docker` prints the resolved result, which is where an
inherited mapping shows up.

## E2E tests

`./ops/icbops test e2e` runs them inside the vue container, through the stack's
Traefik, against `https://app.test.localhost:8443`.
[Test Environment](../testing/environment.md#playwright-runs-inside-the-checkouts-test-stack)
explains how Chromium there reaches Traefik.

`npm run test:e2e` on the host fails at once with `The test stack publishes no
ports`. `ICB_TEST_STACK` is set only inside the vue container. Setting
`E2E_ENV=dev` points a host run at `https://app.docker.localhost` instead,
which is what `npm run test:e2e:dev` and `npm run test:e2e:ui` do.
`frontend/playwright.config.ts` and `frontend/e2e/global.setup.ts` are the two
files that read it, and they have to agree.

`Executable doesn't exist at /ms-playwright/...` after a Playwright upgrade
means the vue image tag no longer matches `@playwright/test` in the lockfile.
`tests/playwright-image-version.bats` fails on that before e2e does.

Hitting the Vue container's port directly bypasses the proxy. CORS and the auth
middleware live in the proxy, so a test that passes there can still fail in a
browser.

E2E is smoke-level by design. Each page keeps a CORS check, a page load, sidebar
navigation and one CRUD roundtrip. Interaction-heavy cases live in the component
tests under `frontend/src/views/__tests__/`, and every E2E file names its
counterpart in a comment.

Selectors are `data-testid`, never CSS classes or DOM structure. Assertions
check generic keywords like `added` or `deleted`, never exact notification
text. Both keep a test from breaking on a restyle or a reworded message.

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

## A test passes locally and fails in CI

pytest runs the same way in CI as on a workstation. Each session starts its own
Postgres and Redis on the runner's Docker, so a CI-only pytest failure is rarely
about the containers.

The e2e job runs `./ops/icbops testing start` and `./ops/icbops test e2e`, the
commands a workstation runs. Under `CI=true`, `icbops` adds
`docker-compose.ci.yml`, which removes the API's Docker socket mount. Anything
in the stack touching container status behaves differently there. The
Playwright config also retries a failed test and refuses `.only` under CI.

Read `CI=true ./ops/icbops testing docker` before blaming a line in the CI
file. It prints the compose set the job resolves.

## Related

- [Test Environment](../testing/environment.md)
- [Testing Configuration](../testing/test_configuration.md)
- [Docker Compose Architecture](../docker/docker-compose.md)
- [Docker troubleshooting](docker-issues.md)
