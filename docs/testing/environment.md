# Test Environment Configuration

This document details how the test environments are configured, set up, and managed in the ichrisbirch project's testing infrastructure.

## Overview

Two suites need two different environments, and neither environment is shared between checkouts.

- **pytest** needs Postgres and Redis. Every session starts its own pair with [testcontainers](https://testcontainers-python.readthedocs.io/), on ports Docker picks, through `PrivateServices` in `tests/environment.py`. The API runs in-process through FastAPI's `TestClient`.
- **Playwright** needs the whole app behind Traefik. It runs inside the checkout's test stack, a Docker Compose project that `./ops/icbops test e2e` starts when it is down.

So two worktrees run either suite at the same time, and neither truncates the other's tables or serves the other's code.

## pytest Runs Against Its Own Postgres and Redis

A pytest session makes its environment ready in two fixtures, both session-scoped and defined in `tests/conftest.py`.

### `setup_test_environment` starts the services and brings the schema to head

It enters `PrivateServices(test_settings)`:

1. It starts a Redis and a Postgres container from the images production runs, which it reads from `docker-compose.yml`. Postgres keeps its data on tmpfs with `fsync`, `synchronous_commit` and `full_page_writes` off, and Redis persists nothing.
2. It points `test_settings` at the ports Docker published for them. Nothing builds an engine or a Redis client at import time, so every later connection reaches them.
3. It runs `full_initialization()` from `ichrisbirch/database/initialization.py`. That migrates the database to head, creates the APScheduler jobstore table, and inserts the admin settings row and the default users.

testcontainers' reaper container (Ryuk) removes both when the session ends, however it ends, including a killed process. A container that fails to start ends the session through `pytest.exit`, after stopping the one that did start.

Readiness is polled every 100 ms rather than testcontainers' default of every second.

The migrations run inside the pytest process. `alembic_config()` passes `configure_logger=False`, so `alembic/env.py` skips `fileConfig`, which would otherwise disable every logger the process already created. alembic's own records reach stderr through the root handler `ichrisbirch/logger.py` installs.

### `truncate_tables` resets the data

It truncates every table, then re-inserts the rows the app cannot run without. The migrations seed rows the suite must not see, which is why it runs on a database that was just created. Its body in `tests/conftest.py` lists the rows. `insert_users_for_login` then adds the login users that tests authenticate as, from `get_test_login_users` in `tests/utils/database.py`.

## Playwright Runs Inside the Checkout's Test Stack

```text
checkout A                          checkout B
  icbops test e2e                     icbops test e2e
    │ compose exec vue                  │
    ▼                                   ▼
  project icb-test-A                  project icb-test-B
    vue (Playwright image)              vue (Playwright image)
      Chromium ── MAP → traefik:8443      Chromium ── MAP → traefik:8443
      traefik ──→ api:8000                traefik ──→ api:8000
              ──→ vue:5173                        ──→ vue:5173
    postgres  redis  scheduler          postgres  redis  scheduler
  nothing published to the host
```

`ops/icbops` names the project `icb-test-<checkout directory>`, lowercased to what compose accepts. Compose scopes the containers (`icb-test-<checkout>-api`), the networks and the node_modules volume to it. Nothing is published to the host, so any number of stacks run side by side.

The browser runs inside the stack for one reason. Chromium in the host's network namespace watches the host's interfaces, and every container that starts or stops anywhere on the machine adds or removes one. Chromium reads that as a network change and aborts its in-flight requests with `ERR_NETWORK_CHANGED`. Inside the vue container it sees only that container's interfaces.

Three pieces route the in-stack browser to Traefik:

- **Traefik listens on 8443**, so the URLs are the ones the app, the CORS origins and the CSP already name: `https://app.test.localhost:8443` and `https://api.test.localhost:8443`.
- **Traefik carries the network aliases `api.test.localhost` and `app.test.localhost`.** Node's own requests in `e2e/global.setup.ts` resolve through Docker's DNS.
- **`playwright.config.ts` launches Chromium with `--host-resolver-rules=MAP *.test.localhost traefik`.** Chromium answers every `*.localhost` name from loopback without asking DNS, so an alias alone never reaches it.

Test Traefik reads its routers and services from files alone, `deploy-containers/traefik/dynamic/test/`. A Docker provider watches the whole daemon and would merge every checkout's `api` into one load balancer. `services.yml` names `http://api:8000` and `http://vue:5173`, which resolve only on the project's own network.

The vue service runs Playwright's image, `mcr.microsoft.com/playwright:v<version>-noble`. That image carries Node and the browsers, so the dev server and the suite share one container and one node_modules. Its tag must equal `@playwright/test` in `frontend/package-lock.json`, because the package launches only its own browser build. `tests/playwright-image-version.bats` holds them level.

`icbops test e2e` runs `npx playwright test` there through `docker compose exec`, as your user, so traces and screenshots in `frontend/test-results/` are yours. The JSON report lands in `.test-reports/playwright-report.json`, through a bind mount of the checkout's `.test-reports/`. The container sets `ICB_TEST_STACK=true`. Without it, `playwright.config.ts` refuses to run and names `./ops/icbops test e2e`, so a host run fails at once rather than timing out against ports that no longer exist.

### What the host cannot do

- Browse the test app. The dev stack is the one to browse.
- Run Playwright headed or in UI mode against the test stack. Traces open on the host with `npx playwright show-trace`.
- Reach the stack's Postgres or Redis by port. `docker exec -it icb-test-<checkout>-postgres psql -U postgres ichrisbirch` is the way in, and `./ops/icbops testing start` prints it.

### Stack lifecycle

| Verb | What it does |
| --- | --- |
| `testing start` | Removes every `icb-test-*` stack whose checkout directory is gone, brings this one up with `up --wait`, then initializes its database |
| `testing ensure` | Starts the stack unless every service with a health check reads `healthy` |
| `testing stop` | `down --volumes` on this checkout's project alone |
| `testing restart` / `rebuild` | As for dev, scoped to this project, each ending in database initialization |
| `test e2e [spec] [args]` | `testing ensure`, then Playwright in the vue container |

The project name comes from the directory name, so two clones sharing one would share a stack. Every verb but `testing stop` refuses a stack another checkout started, and names the `stop`/`start` pair that takes it over.

The stack's Postgres keeps its data on tmpfs, so every stop or recreate empties it. pytest never touches it, so e2e data accumulates between runs until the stack is stopped. The specs create what they assert on, and consecutive runs pass on one database.

A new checkout's first `test e2e` starts its stack from nothing, including a full `npm install` into an empty node_modules volume. A stack holds its memory until `testing stop`, which `docker stats` shows per container.

## Running Tests Locally

```bash
# Run all Python tests
./ops/icbops test run

# Run specific tests
./ops/icbops test run tests/ichrisbirch/api/endpoints/test_tasks.py

# A bare pytest does the same, without writing the reports
uv run pytest tests/ichrisbirch/api/endpoints/test_tasks.py::test_create -v

# Run the e2e suite, or one spec
./ops/icbops test e2e
./ops/icbops test e2e e2e/tasks.spec.ts --trace on
```

`test run` writes `.test-reports/pytest-output.log` and `.test-reports/pytest-report.json` in the checkout. `test e2e` writes `.test-reports/playwright-report.json`.

### Database Lifecycle

| Operation | What it does | When |
| --- | --- | --- |
| **Initialize** (`db init`) | Migrate to head, create the jobstore table, insert the admin settings row and the default users. Idempotent. | Every pytest session, and the end of every `testing start`, `testing restart` and `testing rebuild` |
| **Reset** (`testing db reset`) | Drop every schema, then initialize from scratch, inside the stack's api container | Manual only — a corrupt schema, or a migration edited after it was applied |
| **Seed** (`testing db seed`) | Generated data, inside the stack's api container | Manual only |
| **Truncate** (`truncate_tables` fixture) | TRUNCATE all tables, re-insert the rows the app cannot run without | Start of every pytest session |

The migrations create every schema they write into, so a database needs nothing created ahead of `alembic upgrade head`.

## CI Environment Behavior

The Python job runs pytest on the runner, which starts its own Postgres and Redis exactly as a workstation does. It needs nothing but Docker and the decrypted `.env`.

The e2e job runs `./ops/icbops testing start` and then `./ops/icbops test e2e`, the same commands as a workstation. Under `CI=true`, `icbops` adds `docker-compose.ci.yml`, which drops the API's Docker socket mount, and passes `CI` into the vue container, where the Playwright config turns on retries and forbids `.only`. On a runner the checkout directory is the repository's name, so the project is `icb-test-ichrisbirch`.

## Troubleshooting

### Containers Not Starting

```bash
./ops/icbops testing status
./ops/icbops testing logs
```

### Database Connection Issues

```bash
./ops/icbops testing health
./ops/icbops testing logs postgres
```

### pytest cannot start its services

`Could not start the Postgres and Redis this session runs against` means Docker refused a container. `docker info` says whether the daemon answers.

### CI Failures

```bash
gh run view <run-id> --log-failed
./scripts/track-gh-actions-workflow.sh logs
```

[Testing Environment Troubleshooting](../troubleshooting/testing-issues.md) covers setup failures by their error message.

## Configuration Files

| File | Purpose |
| --- | --- |
| `docker-compose.yml` | Base service definitions, and the images pytest's services use |
| `docker-compose.test.yml` | The per-checkout test stack: project-scoped names, no ports, Playwright's image for vue |
| `docker-compose.ci.yml` | CI-specific overrides, added by `icbops` under `CI=true` |
| `deploy-containers/traefik/dynamic/test/` | Test Traefik's routers, services, middlewares and TLS |
| `tests/environment.py` | `PrivateServices`, pytest's Postgres and Redis |
| `tests/conftest.py` | Pytest fixtures |
| `tests/utils/database.py` | Test settings |
| `frontend/playwright.config.ts` | The e2e suite's URLs and Chromium's resolver rule |

## Fixtures Reference

### Session-Scoped (run once per test session)

| Fixture | Purpose |
| --- | --- |
| `setup_test_environment` | Start this session's Postgres and Redis, initialize the database |
| `truncate_tables` | Truncate every table, re-insert the rows the app cannot run without |
| `insert_users_for_login` | Create test login users |

### Module-Scoped (run once per test file)

| Fixture | Purpose |
| --- | --- |
| `test_api` | Unauthenticated API client |
| `test_api_logged_in` | Authenticated regular user |
| `test_api_logged_in_admin` | Authenticated admin user |

### Function-Scoped (run once per test)

Same fixtures with `_function` suffix for test isolation.
