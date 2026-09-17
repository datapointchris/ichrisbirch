# Test Environment Configuration

This document details how the test environment is configured, set up, and managed in the ichrisbirch project's testing infrastructure.

## Overview

The test environment uses Docker Compose to provide isolated, reproducible infrastructure for running pytest. The `DockerComposeTestEnvironment` class manages the lifecycle of these containers.

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

## DockerComposeTestEnvironment Class

Located in `tests/environment.py`, this class manages the Docker Compose test environment.

### Key Features

- **Container reuse:** Reuses running test containers, starts them when they are not running
- **CI detection:** Expects containers the workflow already started when running in GitHub Actions
- **Health checking:** Waits for Postgres, Redis and the API to respond
- **Database readiness:** Brings the database to the current schema, then truncates it

### Lifecycle Methods

#### `setup()`

Called once at the start of the test session by the `setup_test_environment` fixture:

1. **CI:** Verify the containers the workflow started are running.
2. **Local:** Reuse running `postgres`, `redis` and `api` containers, or run `docker compose up -d` and wait for them.
3. **Initialize:** `full_initialization()` creates missing schemas, migrates to head, creates the APScheduler jobstore table, and inserts the default users.
4. **Truncate:** Truncate every table, then re-insert lookup data and the default users.

```python
def setup(self):
    if self.is_ci:
        if not self.docker_test_services_already_running():
            ...  # wait once, then raise
    else:
        if self.docker_test_services_already_running():
            self.verify_test_services()
        else:
            self.setup_test_services()

    full_initialization(self.settings)
    self.truncate_test_database()
```

Step 3 runs on every session. The test Postgres keeps its data on tmpfs, so a container that was stopped or recreated holds an empty database while every health check passes. Initialization is idempotent, so a database already at head passes through unchanged. A new migration is applied at the next session without restarting anything.

Migrations run inside the pytest process. `_get_alembic_config()` passes `configure_logger=False`, so `alembic/env.py` skips `fileConfig`. That call would otherwise disable every logger the test process had already created.

Any exception during setup ends the session through `pytest.exit`.

#### `teardown()`

Leaves the containers running, so the next session reuses them. Stop them with `./ops/icbops testing stop`.

## Running Tests Locally

### Container Reuse

```bash
# Run all tests (starts containers if needed)
./ops/icbops test run

# Run specific tests
./ops/icbops test run tests/ichrisbirch/api/endpoints/test_tasks.py

# Run with verbose output
./ops/icbops test run -v
```

`icbops test run` reuses the stack when `icb-test-api` reports `healthy`. Otherwise it removes any existing test containers and runs `testing start`. Container health says nothing about the schema, so pytest's session setup initializes the database either way.

This approach provides:

- **Reliability:** Each test run gets a clean database state
- **Speed:** TRUNCATE is sub-second vs seconds for drop/recreate
- **No stale connections:** Schema is preserved, so the API container's connection pool stays valid
- **Predictable behavior:** Same behavior every time

### Database Lifecycle

The test database has two CLI operations and two internal operations:

| Operation | What it does | When |
| --- | --- | --- |
| **Initialize** (`db init`) | Create missing schemas, migrate to head, create the jobstore table, insert default users. Idempotent. | End of every `testing start`, `testing restart` and `testing rebuild` |
| **Initialize** (pytest session setup) | The same `full_initialization()` | Start of every pytest session |
| **Reset** (`db reset`) | Drop everything + initialize from scratch | Manual only — a corrupt schema, or a migration edited after it was applied |
| **Truncate** (pytest session setup) | TRUNCATE all tables, re-insert lookup data and default users | Start of every pytest session |

Truncation preserves the schema, so the API container's connection pool stays valid — no container restart needed.

### Network Isolation

Test and dev environments use separate proxy networks to avoid conflicts:

- **Development:** `icb-dev-proxy` network
- **Testing:** `icb-test-proxy` network

This allows both environments to run simultaneously without Traefik routing conflicts.

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

### Direct Docker Compose Commands

```bash
# Stop containers
docker compose -f docker-compose.yml -f docker-compose.test.yml \
  --project-name icb-test down -v
```

## Test Environment vs Development Environment

The test and development environments can run simultaneously on different ports:

| Service | Dev Port | Test Port |
| --- | --- | --- |
| PostgreSQL | 5432 | 5434 |
| Redis | 6379 | 6380 |
| API | 8000 | 8001 |
| Vue | 5173 | 5174 |
| Traefik HTTPS | 443 | 8443 |

This allows you to run tests without stopping your development environment.

## CI Environment Behavior

In GitHub Actions, the environment behaves differently:

### Workflow Pre-starts Containers

The CI workflow starts containers and initializes the database before pytest runs:

```yaml
- name: Start test services
  run: |
    docker compose ... --project-name icb-test up -d --build --wait --wait-timeout 120 postgres redis
    docker compose ... --project-name icb-test up -d --build --wait --wait-timeout 180 api scheduler

- name: Initialize test database
  run: uv run python -m ichrisbirch.database.initialization --env testing --db-host localhost --db-port 5434
```

### Test Fixtures Skip Container Management

```python
if self.is_ci:
    logger.info('Running in CI environment - containers should be pre-started by workflow')
    # Just verify they're running, don't try to start
```

Session setup still initializes and truncates the database in CI. Initialization finds the database already at head.

### CI Override File

The `docker-compose.ci.yml` file adjusts the test stack for the runner:

- The API drops the Docker socket bind mount
- Vue skips the image build and allows a longer health check start period for a cold `npm install`
- Traefik runs with the dashboard disabled
- The proxy network is created by Compose rather than expected to exist

## Database Configuration

### In-Memory Database

The test environment uses tmpfs for PostgreSQL:

```yaml
postgres:
  environment:
    - PGDATA=/tmp/postgres
  tmpfs:
    - /tmp/postgres
  command: >
    postgres
    -c fsync=off
    -c synchronous_commit=off
    -c full_page_writes=off
```

This provides:

- Fast writes (no disk I/O)
- An empty database whenever the container stops or is recreated
- No persistence between container lifetimes

### Test Users

The fixture `insert_users_for_login` creates test users:

| User | Email | Role | Purpose |
| --- | --- | --- | --- |
| Test User to be Sacrificed for Delete Test | <sacrifice@testgods.com> | User | Deleted by the users endpoint tests |
| Test Login Regular User | <testloginregular@testuser.com> | User | Regular user tests |
| Test Login Admin User | <testloginadmin@testadmin.com> | Admin | Admin-only tests |

## Health Checks

### Service Health Check

The environment checks that the containers it needs are running:

```python
def docker_test_services_already_running(self, required_services=None) -> bool:
    """Returns True if all required Docker Compose services are running."""
    if required_services is None:
        required_services = {'postgres', 'redis', 'api'}
```

`verify_test_services()` then waits for Postgres and Redis to accept a socket connection and for the API's `/health` to return 200. None of these checks read the schema, which is why setup initializes the database after them.

## Troubleshooting

### Containers Not Starting

```bash
# Check container status
./ops/icbops testing status

# View logs
./ops/icbops testing logs
```

### Database Connection Issues

```bash
# Full diagnostic health check
./ops/icbops testing health

# Postgres logs
./ops/icbops testing logs --service postgres
```

### Port Conflicts

If ports 5434, 6380, etc. are in use:

```bash
# Find what's using the port
lsof -i :5434

# Stop conflicting process or change test ports
```

### CI Failures

Check the CI workflow logs:

```bash
# View failed job logs
gh run view <run-id> --log-failed

# Or use the tracking script
./scripts/track-gh-actions-workflow.sh logs
```

## Configuration Files

| File | Purpose |
| --- | --- |
| `docker-compose.yml` | Base service definitions |
| `docker-compose.test.yml` | Test-specific overrides (ports, tmpfs) |
| `docker-compose.ci.yml` | CI-specific overrides (no local mounts) |
| `tests/environment.py` | Test environment management |
| `tests/conftest.py` | Pytest fixtures |
| `tests/utils/database.py` | Database utilities and test settings |

## Fixtures Reference

### Session-Scoped (run once per test session)

| Fixture | Purpose |
| --- | --- |
| `setup_test_environment` | Start or reuse containers, initialize and truncate the database |
| `truncate_tables` | Manage table lifecycle |
| `insert_users_for_login` | Create test users |

### Module-Scoped (run once per test file)

| Fixture | Purpose |
| --- | --- |
| `test_api` | Unauthenticated API client |
| `test_api_logged_in` | Authenticated regular user |
| `test_api_logged_in_admin` | Authenticated admin user |

### Function-Scoped (run once per test)

Same fixtures with `_function` suffix for test isolation.
