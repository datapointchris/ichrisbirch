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
│  │ Postgres │  │  Redis   │  │   API    │  │   App    │        │
│  │  :5434   │  │  :6380   │  │  :8001   │  │  :5001   │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
│       │             │             │             │               │
│       └─────────────┴─────────────┴─────────────┘               │
│                           │                                     │
│  ┌──────────┐  ┌──────────┴───────┐  ┌──────────┐              │
│  │   Chat   │  │    Scheduler     │  │ Traefik  │              │
│  │  :8507   │  │  (creates jobs)  │  │  :8443   │              │
│  └──────────┘  └──────────────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

## DockerComposeTestEnvironment Class

Located in `tests/environment.py`, this class manages the Docker Compose test environment.

### Key Features

- **Docker Compose orchestration:** Starts/stops all test containers
- **CI detection:** Adjusts behavior when running in GitHub Actions
- **Health checking:** Waits for services to be ready
- **Database initialization:** Creates tables and test users

### Class Structure

```python
class DockerComposeTestEnvironment:
    # Compose file combinations
    COMPOSE_FILES = '-f docker-compose.yml -f docker-compose.test.yml'
    COMPOSE_FILES_CI = '-f docker-compose.yml -f docker-compose.test.yml -f docker-compose.ci.yml'

    @property
    def is_ci(self) -> bool:
        """Detect if running in CI environment."""
        return os.environ.get('CI', '').lower() == 'true'

    def setup(self):
        """Start containers and initialize database."""

    def teardown(self):
        """Stop containers (skipped in CI)."""
```

### Lifecycle Methods

#### `setup()`

Called at the start of the test session:

1. **CI check:** If in CI, verify containers are already running
2. **Local check:** If containers not running, start them
3. **Database init:** Create tables and insert test users

```python
def setup(self):
    if self.is_ci:
        # CI: Containers pre-started by workflow
        if not self.docker_test_services_already_running():
            raise RuntimeError('CI containers not running')
    elif not self.docker_test_services_already_running():
        # Local: Start containers ourselves
        self.setup_test_services()

    self.ensure_database_ready()
```

#### `teardown()`

Called at the end of the test session:

```python
def teardown(self):
    if self.is_ci:
        # CI: Cleanup handled by workflow
        return
    # Local: Stop containers
    self.stop_docker_compose()
```

## Running Tests Locally

### Starting the Test Environment

```bash
# Recommended: Use the CLI
./cli/ichrisbirch testing start

# Or let pytest start it automatically
uv run pytest  # DockerComposeTestEnvironment.setup() handles it
```

### Running Tests

```bash
# All tests
uv run pytest

# Specific file
uv run pytest tests/ichrisbirch/api/endpoints/test_tasks.py

# Specific test
uv run pytest tests/ichrisbirch/api/endpoints/test_tasks.py::test_create -v

# With coverage
uv run pytest --cov=ichrisbirch
```

### Stopping the Test Environment

```bash
# Via CLI
./cli/ichrisbirch testing stop

# Or directly
docker compose -f docker-compose.yml -f docker-compose.test.yml \
  --project-name ichrisbirch-testing down -v
```

## Test Environment vs Development Environment

The test and development environments can run simultaneously on different ports:

| Service | Dev Port | Test Port |
|---------|----------|-----------|
| PostgreSQL | 5432 | 5434 |
| Redis | 6379 | 6380 |
| API | 8000 | 8001 |
| App | 5000 | 5001 |
| Chat | 8505 | 8507 |
| Traefik HTTPS | 443 | 8443 |

This allows you to run tests without stopping your development environment.

## CI Environment Behavior

In GitHub Actions, the environment behaves differently:

### Workflow Pre-starts Containers

The CI workflow starts containers before pytest runs:

```yaml
- name: Start Docker Compose test environment
  run: |
    docker compose ... up -d --build postgres redis
    sleep 10
    docker compose ... up -d --build api app chat scheduler
    sleep 30
```

### Test Fixtures Skip Container Management

```python
if self.is_ci:
    logger.info('Running in CI - containers should be pre-started')
    # Just verify they're running, don't try to start
```

### CI Override File

The `docker-compose.ci.yml` file removes local-only configurations:

- No AWS credentials bind mount (uses env vars)
- Internal bridge network (not external)
- Traefik dashboard disabled

## Database Configuration

### In-Memory Database

The test environment uses tmpfs for PostgreSQL:

```yaml
postgres:
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
- Fresh database each run
- No persistence between runs

### Test Users

The fixture `insert_users_for_login` creates test users:

| User | Email | Role | Purpose |
|------|-------|------|---------|
| Test User | <testlogin@test.com> | User | Regular user tests |
| Test Admin | <testloginadmin@testadmin.com> | Admin | Admin-only tests |

## Health Checks

### Service Health Check

The environment waits for services to be healthy:

```python
def docker_test_services_already_running(self, required_services=None):
    """Check if required Docker services are running."""
    if required_services is None:
        required_services = ['postgres', 'redis', 'api', 'app']
    # Check each service status
```

### Database Health Check

```python
def ensure_database_ready(self):
    """Wait for database to accept connections and create tables."""
    # Retry connection with backoff
    # Create all SQLAlchemy tables
    # Insert test users
```

## Troubleshooting

### Containers Not Starting

```bash
# Check container status
docker compose -f docker-compose.yml -f docker-compose.test.yml \
  --project-name ichrisbirch-testing ps

# View logs
docker compose -f docker-compose.yml -f docker-compose.test.yml \
  --project-name ichrisbirch-testing logs
```

### Database Connection Issues

```bash
# Test database connection
docker compose exec postgres psql -U postgres -d ichrisbirch -c "SELECT 1"

# Check postgres logs
docker compose logs postgres
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
|------|---------|
| `docker-compose.yml` | Base service definitions |
| `docker-compose.test.yml` | Test-specific overrides (ports, tmpfs) |
| `docker-compose.ci.yml` | CI-specific overrides (no local mounts) |
| `tests/environment.py` | Test environment management |
| `tests/conftest.py` | Pytest fixtures |
| `tests/utils/database.py` | Database utilities and test settings |

## Fixtures Reference

### Session-Scoped (run once per test session)

| Fixture | Purpose |
|---------|---------|
| `setup_test_environment` | Start Docker Compose, create tables |
| `create_drop_tables` | Manage table lifecycle |
| `insert_users_for_login` | Create test users |

### Module-Scoped (run once per test file)

| Fixture | Purpose |
|---------|---------|
| `test_api` | Unauthenticated API client |
| `test_api_logged_in` | Authenticated regular user |
| `test_api_logged_in_admin` | Authenticated admin user |
| `test_app` | Flask test client |
| `test_app_logged_in` | Flask client with session |

### Function-Scoped (run once per test)

Same fixtures with `_function` suffix for test isolation.
