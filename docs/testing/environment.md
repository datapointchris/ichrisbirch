# Test Environment Configuration

This document details how the test environment is configured, set up, and managed in the ichrisbirch project's testing infrastructure.

## Overview

The test environment uses Docker Compose to provide isolated, reproducible infrastructure for running pytest. The `DockerComposeTestEnvironment` class in `tests/environment.py` manages the lifecycle of these containers.

## Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                    Test Environment                             │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Postgres │  │  Redis   │  │   API    │  │   Vue    │        │
│  │  :5434   │  │  :6380   │  │  :8001   │  │  :5174   │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
│       │             │             │             │               │
│       └─────────────┴─────────────┴─────────────┘               │
│                           │                                     │
│                ┌──────────┴───────┐  ┌──────────┐              │
│                │    Scheduler     │  │ Traefik  │              │
│                │  (creates jobs)  │  │  :8443   │              │
│                └──────────────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

Ports and service definitions are in `docker-compose.test.yml`.

## Session Setup

A pytest session makes the environment ready in two fixtures, both session-scoped and defined in `tests/conftest.py`.

### `setup_test_environment` makes the stack and schema ready

It calls `DockerComposeTestEnvironment.setup()`:

1. **In CI**, it verifies that the containers the workflow started are running.
2. **Locally**, it reuses running `postgres`, `redis` and `api` containers, or starts them with `docker compose up -d`. `verify_test_services()` then waits for Postgres and Redis to accept a socket connection and for the API's `/health` to return 200.
3. **In both**, it runs `full_initialization()` from `ichrisbirch/database/initialization.py`. That migrates the database to head, creates the APScheduler jobstore table, and inserts the default users.

Step 3 runs on every session. The test Postgres keeps its data on tmpfs, so a container that was stopped or recreated holds an empty database while every health check passes. Initialization is idempotent, so a database already at head passes through unchanged, and a new migration reaches pytest without restarting anything.

The migrations run inside the pytest process. `_get_alembic_config()` passes `configure_logger=False`, so `alembic/env.py` skips `fileConfig`, which would otherwise disable every logger the process already created. alembic's own records reach stderr through the root handler `ichrisbirch/logger.py` installs.

Any exception during setup ends the session through `pytest.exit`.

When the session ends, `teardown()` leaves the containers running, so the next session reuses them. Stop them with `./ops/icbops testing stop`.

### `truncate_tables` resets the data

It truncates every table, then inserts the lookup data and the default users. `insert_users_for_login` then adds the login users that tests authenticate as, from `get_test_login_users` in `tests/utils/database.py`. Truncation preserves the schema, so the API container's connection pool stays valid.

## Running Tests Locally

```bash
# Run all tests (starts containers if needed)
./ops/icbops test run

# Run specific tests
./ops/icbops test run tests/ichrisbirch/api/endpoints/test_tasks.py

# Run with verbose output
./ops/icbops test run -v
```

`icbops test run` reuses the stack when `icb-test-api` reports `healthy`. Otherwise it removes any existing test containers and runs `testing start`. Container health says nothing about the schema, so session setup initializes the database either way.

### Database Lifecycle

| Operation | What it does | When |
| --- | --- | --- |
| **Initialize** (`db init`) | Migrate to head, create the jobstore table, insert default users. Idempotent. | End of every `testing start`, `testing restart` and `testing rebuild`, and every pytest session |
| **Reset** (`db reset`) | Drop every schema, then initialize from scratch | Manual only — a corrupt schema, or a migration edited after it was applied |
| **Truncate** (`truncate_tables` fixture) | TRUNCATE all tables, re-insert lookup data and default users | Start of every pytest session |

The migrations create every schema they write into, so a database needs nothing created ahead of `alembic upgrade head`.

### One Stack, Shared by Every Checkout

The test containers have fixed names, so every checkout on a machine runs against the same database. A session from a checkout carrying a new migration upgrades that database. A later session from a checkout without that migration then stops in setup with `Can't locate revision identified by '<revision>'`. `./ops/icbops testing stop && ./ops/icbops testing start` from the checkout you are testing gives it a database migrated by its own history.

### Network Isolation

The test stack's proxy network is `icb-test-proxy` and the dev stack's is `icb-dev-proxy`, so both can run at once without Traefik routing conflicts.

### Manual Environment Management

For extended debugging sessions, you can manage the environment manually:

```bash
# Start containers manually (stays running)
./ops/icbops testing start

# Run pytest directly (uses existing containers)
uv run pytest tests/ichrisbirch/api/endpoints/test_tasks.py::test_create -v

# Stop when done
./ops/icbops testing stop
```

## CI Environment Behavior

The `Start test services` and `Initialize test database` steps in `.github/workflows/validate.yml` start the containers and initialize the database before pytest runs. `setup()` detects CI through `CI=true` and only verifies the containers are running. Session setup still initializes the database, and finds it already at head.

`docker-compose.ci.yml` adjusts the test stack for the runner: it drops the API's Docker socket mount, skips the Vue image build, disables the Traefik dashboard, and lets Compose create the proxy network.

## Database Configuration

The `postgres` service in `docker-compose.test.yml` keeps `PGDATA` on tmpfs and turns off `fsync`, `synchronous_commit` and `full_page_writes`. Writes skip disk I/O, and the database empties whenever the container stops or is recreated.

## Troubleshooting

### Containers Not Starting

```bash
./ops/icbops testing status
./ops/icbops testing logs
```

### Database Connection Issues

```bash
./ops/icbops testing health
./ops/icbops testing logs --service postgres
```

### Port Conflicts

If ports 5434, 6380, etc. are in use:

```bash
# Find what's using the port
lsof -i :5434
```

### CI Failures

```bash
gh run view <run-id> --log-failed
./scripts/track-gh-actions-workflow.sh logs
```

[Testing Environment Troubleshooting](../troubleshooting/testing-issues.md) covers setup failures by their error message.

## Configuration Files

| File | Purpose |
| --- | --- |
| `docker-compose.yml` | Base service definitions |
| `docker-compose.test.yml` | Test-specific overrides (ports, tmpfs) |
| `docker-compose.ci.yml` | CI-specific overrides |
| `tests/environment.py` | Test environment management |
| `tests/conftest.py` | Pytest fixtures |
| `tests/utils/database.py` | Database utilities and test settings |

## Fixtures Reference

### Session-Scoped (run once per test session)

| Fixture | Purpose |
| --- | --- |
| `setup_test_environment` | Start or reuse containers, initialize the database |
| `truncate_tables` | Truncate every table, re-insert lookup data and default users |
| `insert_users_for_login` | Create test login users |

### Module-Scoped (run once per test file)

| Fixture | Purpose |
| --- | --- |
| `test_api` | Unauthenticated API client |
| `test_api_logged_in` | Authenticated regular user |
| `test_api_logged_in_admin` | Authenticated admin user |

### Function-Scoped (run once per test)

Same fixtures with `_function` suffix for test isolation.
