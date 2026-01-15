# Testing Environment Troubleshooting

This document addresses issues encountered when setting up and running tests in the iChrisBirch project, particularly with Docker-based testing environments and database configuration.

## Recent Critical Issues

### Docker Network Conflicts During Testing

**Problem:** Test runs fail with Docker networking errors like:

```text
Error response from daemon: failed to set up container networking: network [network-id] not found
```

**Error Messages:**

```text
Error response from daemon: failed to set up container networking: network 0c3cd93080df5b4a0c4308df29659328a317c458853c34c473470e35abf5f31a not found
✗ Tests failed (exit code: 1)
```

**Root Cause:** Previous test runs left orphaned Docker containers, networks, and volumes that weren't properly cleaned up. The original cleanup in the CLI script was:

```bash
docker-compose -f docker-compose.yml -f docker-compose.test.yml down -v >/dev/null 2>&1
```

This silently suppressed cleanup errors, so failed cleanup operations went unnoticed, leading to resource conflicts on subsequent test runs.

**Attempted Solutions (That Failed):**

- Running `docker system prune` manually between tests - temporary fix but not automated
- Checking for specific container names only - missed containers with dynamic names  
- Using docker-compose down without additional cleanup - didn't handle edge cases where compose cleanup failed

**Resolution:** Implemented container reuse strategy with database reset:

**Test run command** (`cli/ichrisbirch:208-259`):

```bash
function test-run() {
  cd "$ICHRISBIRCH_HOME" || exit
  source "$ICHRISBIRCH_HOME/.venv/bin/activate"
  export ENVIRONMENT=testing

  # Check if containers are already running and healthy
  local containers_ready=false
  if $COMPOSE_TEST ps --status running -q 2>/dev/null | grep -q .; then
    echo "Test containers already running, checking health..."
    if $COMPOSE_TEST ps | grep -q "healthy"; then
      containers_ready=true
      echo "Containers healthy, reusing them"
    else
      echo "Containers unhealthy, restarting..."
      $COMPOSE_TEST down --volumes 2>/dev/null || true
    fi
  fi

  if [ "$containers_ready" = false ]; then
    ensure-proxy-network
    echo "Starting test containers..."
    $COMPOSE_TEST up -d
    sleep 15
  fi

  # Always reset database to ensure clean state
  echo "Initializing test database..."
  ENVIRONMENT=testing uv run python -m ichrisbirch.database.initialization \
    --env testing --db-host localhost --db-port 5434

  # Run pytest
  uv run pytest "$@"

  # Leave containers running for fast iteration
  echo "Containers left running for fast iteration."
  echo "Stop them with: icb testing stop"
}
```

**Key improvements:**

1. **Container reuse**: Reuses healthy containers instead of recreating them each run
2. **Health checking**: Verifies container health before reusing
3. **Database reset**: Always reinitializes database for clean test state
4. **Fast iteration**: Leaves containers running after tests for quick re-runs
5. **Unhealthy recovery**: Restarts containers if they're unhealthy

**Prevention:** The container reuse approach prevents network conflicts because containers are not constantly being created and destroyed. The database reset ensures clean state without the overhead of container recreation.

**Manual cleanup when needed:**

```bash
# Stop and remove all test containers and volumes
./cli/ichrisbirch testing stop

# Full Docker cleanup if issues persist
docker compose -f docker-compose.yml -f docker-compose.test.yml \
  --project-name icb-test down -v --remove-orphans
docker network prune -f
```

## Test Database Setup Issues

### Schema Creation Failures

**Problem:** Tests fail because the database schema doesn't exist.

**Error Messages:**

```text
psycopg2.errors.InvalidSchemaName: schema "ichrisbirch_test" does not exist
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedTable) relation "users" does not exist
```

**Root Cause:** Test database doesn't have the required schema or tables created.

**Resolution:**

1. **Ensure schema environment variable is set:**

```yaml
# docker-compose.test.yml
services:
  test-runner:
    environment:
      - POSTGRES_DB_SCHEMA=ichrisbirch_test
      - DATABASE_URL=postgresql://ichrisbirch:password@postgres:5432/ichrisbirch_test
```

1. **Run Alembic migrations in test setup:**

```python
# In your test configuration
from alembic import command
from alembic.config import Config
from ichrisbirch.database import get_sqlalchemy_session

def setup_test_database():
    # Run migrations to create schema
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
```

1. **Verify database connection:**

```bash
# Test database connectivity
docker-compose -f docker-compose.test.yml run test-runner uv run python -c "
from ichrisbirch.config import settings
print(f'Database URL: {settings.database_url}')
"
```

### Test Data Isolation Issues

**Problem:** Tests interfere with each other due to shared test data.

**Symptoms:**

- Tests pass individually but fail when run together
- Inconsistent test results
- Foreign key constraint violations

**Resolution:**

Use proper test fixtures with cleanup:

```python
@pytest.fixture(autouse=True)
def insert_testing_data():
    """Setup test data before each test module."""
    from ichrisbirch.database.testing import insert_test_data, delete_test_data

    # Setup
    insert_test_data('users', 'habits', 'habitcategories')

    yield

    # Teardown
    delete_test_data('habits', 'habitcategories', 'users')
```

## Docker Test Environment Issues

### Container Startup Problems

**Problem:** Test containers fail to start or exit immediately.

**Common Causes:**

1. **Missing test dependencies:**

```dockerfile
# Ensure test dependencies are installed
FROM builder as development
COPY . .
RUN uv sync --frozen --group dev --group test
```

1. **Database service not ready:**

```yaml
# docker-compose.test.yml
services:
  test-runner:
    depends_on:
      postgres:
        condition: service_healthy

  postgres:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ichrisbirch"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s
```

### Test Command Execution Issues

**Problem:** Pytest command not found or fails to execute.

**Error:** `/app/.venv/bin/pytest: No such file or directory`

**Cause:** Virtual environment issues or missing test runner.

**Resolution:**

Use UV to run tests:

```yaml
# docker-compose.test.yml
services:
  test-runner:
    command: ["uv", "run", "pytest", "-vv", "--cov=ichrisbirch"]
```

Verify pytest is available:

```bash
docker-compose -f docker-compose.test.yml run test-runner uv run which pytest
```

## Coverage and Reporting Issues

### Missing Coverage Reports

**Problem:** Coverage reports are not generated or are empty.

**Common Issues:**

1. **Missing coverage configuration:**

```toml
# pyproject.toml
[tool.coverage.run]
source = ["ichrisbirch"]
omit = [
    "*/tests/*",
    "*/venv/*",
    "*/__pycache__/*"
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError"
]
```

1. **Coverage data location issues:**

```bash
# Ensure coverage data is in correct location
docker-compose -f docker-compose.test.yml run test-runner uv run coverage report
```

### HTML Coverage Reports

**Problem:** HTML coverage reports are not accessible.

**Resolution:**

Mount volume to access reports from host:

```yaml
# docker-compose.test.yml
services:
  test-runner:
    volumes:
      - ./test-results:/app/test-results
    command: ["uv", "run", "pytest", "--cov=ichrisbirch", "--cov-report=html:test-results/coverage"]
```

## Performance and Timeout Issues

### Slow Test Execution

**Problem:** Tests take too long to run, causing timeouts.

**Common Causes:**

1. **Database connection overhead**
1. **Inefficient test data setup**
1. **Missing test database optimization**

**Optimizations:**

```python
# Use database transactions for faster rollback
@pytest.fixture(autouse=True)
def db_transaction():
    """Use transaction rollback instead of DELETE for cleanup."""
    from ichrisbirch.database import get_sqlalchemy_session

    with get_sqlalchemy_session() as session:
        transaction = session.begin()
        yield session
        transaction.rollback()
```

### Memory Issues

**Problem:** Tests fail due to memory limitations.

**Resolution:**

Set appropriate resource limits:

```yaml
# docker-compose.test.yml
services:
  test-runner:
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
```

## Environment-Specific Issues

### Local vs Container Differences

**Problem:** Tests pass locally but fail in containers.

**Common Causes:**

1. **Path differences:** Absolute vs relative paths
1. **Environment variables:** Missing in container
1. **File permissions:** User/group differences

**Resolution:**

1. **Standardize paths:**

```python
# Use pathlib for cross-platform compatibility
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
TEST_DATA_DIR = BASE_DIR / "tests" / "data"
```

1. **Document required environment variables:**

```yaml
# .env.test
POSTGRES_DB_SCHEMA=ichrisbirch_test
DATABASE_URL=postgresql://ichrisbirch:password@postgres:5432/ichrisbirch_test
API_URL=http://api:8000
FLASK_ENV=testing
```

### CI/CD Pipeline Issues

**Problem:** Tests pass locally but fail in GitHub Actions.

**Common Issues:**

1. **Service dependencies not ready**
1. **Different Python/dependency versions**
1. **Missing environment setup**

**Resolution:**

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up test environment
        run: |
          cp .env.test.example .env.test
          docker-compose -f docker-compose.test.yml up -d postgres

      - name: Wait for database
        run: |
          docker-compose -f docker-compose.test.yml run --rm test-runner \
            sh -c 'until pg_isready -h postgres -p 5432; do sleep 1; done'

      - name: Run tests
        run: docker-compose -f docker-compose.test.yml up test-runner
```

## Debugging Test Issues

### Test Failure Diagnosis

**Steps to debug failing tests:**

1. **Run single test in isolation:**

```bash
docker-compose -f docker-compose.test.yml run test-runner \
  uv run pytest tests/specific_test.py::TestClass::test_method -vv
```

1. **Check database state:**

```bash
docker-compose -f docker-compose.test.yml run test-runner \
  uv run python -c "
from ichrisbirch.database import get_sqlalchemy_session
with get_sqlalchemy_session() as session:
    result = session.execute('SELECT COUNT(*) FROM users')
    print(f'Users count: {result.scalar()}')
"
```

1. **Examine test logs:**

```bash
docker-compose -f docker-compose.test.yml logs test-runner
docker-compose -f docker-compose.test.yml logs postgres
```

### Database Connection Debugging

**Test database connectivity:**

```python
# debug_db.py
from ichrisbirch.config import settings
from ichrisbirch.database import get_sqlalchemy_session

print(f"Database URL: {settings.database_url}")

try:
    with get_sqlalchemy_session() as session:
        result = session.execute("SELECT version()")
        print(f"PostgreSQL version: {result.scalar()}")
        print("Database connection successful!")
except Exception as e:
    print(f"Database connection failed: {e}")
```

Run with:

```bash
docker-compose -f docker-compose.test.yml run test-runner uv run python debug_db.py
```

## Prevention Strategies

### Test Environment Validation

Create a test environment validation script:

```python
# validate_test_env.py
import sys
from ichrisbirch.config import settings
from ichrisbirch.database import get_sqlalchemy_session

def validate_test_environment():
    """Validate that test environment is properly configured."""
    errors = []

    # Check required environment variables
    if not settings.database_url:
        errors.append("DATABASE_URL not set")

    if "test" not in settings.database_url:
        errors.append("DATABASE_URL should contain 'test'")

    # Test database connection
    try:
        with get_sqlalchemy_session() as session:
            session.execute("SELECT 1")
    except Exception as e:
        errors.append(f"Database connection failed: {e}")

    if errors:
        print("Test environment validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("Test environment validation passed!")

if __name__ == "__main__":
    validate_test_environment()
```

### Automated Test Environment Setup

```bash
#!/bin/bash
# scripts/setup_test_env.sh

set -e

echo "Setting up test environment..."

# Copy test environment file
cp .env.test.example .env.test

# Build test images
docker-compose -f docker-compose.test.yml build

# Start database
docker-compose -f docker-compose.test.yml up -d postgres

# Wait for database to be ready
echo "Waiting for database..."
docker-compose -f docker-compose.test.yml run --rm test-runner \
  sh -c 'until pg_isready -h postgres -p 5432; do sleep 1; done'

# Run migrations
docker-compose -f docker-compose.test.yml run --rm test-runner \
  uv run alembic upgrade head

# Validate environment
docker-compose -f docker-compose.test.yml run --rm test-runner \
  uv run python validate_test_env.py

echo "Test environment setup complete!"
```

## Common Error Messages and Solutions

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `schema "ichrisbirch_test" does not exist` | Missing schema environment variable | Set `POSTGRES_DB_SCHEMA=ichrisbirch_test` |
| `relation "users" does not exist` | Database migrations not run | Run `alembic upgrade head` |
| `pytest: not found` | Missing test dependencies | Install with `uv sync --group test` |
| `Connection refused` | Database not ready | Add health check and depends_on |
| `permission denied` | File permission issues | Set proper user/group in Docker |
| `No module named 'ichrisbirch'` | Package not installed | Run `uv sync` to install package |
| `error: Failed to spawn: 'pytest'` | Test dependencies not installed in Docker build | Add `--group test` to Dockerfile `uv sync` |
| `service has neither an image nor a build context` | Missing build directive in compose file | Add build context to service definition |
| `ModuleNotFoundError: No module named 'tests.utils.environment'` | Incorrect import path | Fix import path to correct module location |

## Recent Critical Issues (July 2025)

### Test Dependencies Missing in Docker Build

**Problem:** Docker-based test runner fails with `error: Failed to spawn: 'pytest'` even though pytest is defined in pyproject.toml dependency groups.

**Error Messages:**

```bash
test-runner-1  | error: Failed to spawn: `pytest`
test-runner-1  |   Caused by: No such file or directory (os error 2)
test-runner-1 exited with code 2
```

**Root Cause:** The Dockerfile development stage was not installing test dependency groups. The `uv sync --frozen` command only installs main dependencies, not test dependencies.

**Attempted Solutions (That Failed):**

- Manually running `uv sync --group test` in running container worked, but didn't persist in built image
- Rebuilding without `--no-cache` didn't fix the issue
- Installing pytest directly didn't address the underlying group installation problem

**Resolution:**

Update the Dockerfile development stage to include dependency groups:

```dockerfile
# Before (broken):
RUN uv venv && \
    uv sync --frozen && \
    chown -R appuser:appuser /app/.venv /app

# After (working):
RUN uv venv && \
    uv sync --frozen --group dev --group test && \
    chown -R appuser:appuser /app/.venv /app
```

Then rebuild with `--no-cache`:

```bash
docker-compose -f docker-compose.test.yml build --no-cache test-runner
```

**Prevention:** Always include `--group dev --group test` flags when installing dependencies in development/test Docker stages.

### Missing Build Context in Docker Compose Services

**Problem:** Docker Compose fails with "service has neither an image nor a build context specified" for scheduler service.

**Error Messages:**

```text
service "scheduler" has neither an image nor a build context specified: invalid compose project
```

**Root Cause:** The test compose file was overriding the scheduler service configuration but omitted the required `build` directive that was present in the base compose file.

**Resolution:**

Add build context to the problematic service in `docker-compose.test.yml`:

```yaml
# Before (broken):
scheduler:
  command: .venv/bin/python -m ichrisbirch.wsgi_scheduler
  environment:
    - ENVIRONMENT=testing
    # ... other config

# After (working):
scheduler:
  build:
    context: .
    target: development
  command: .venv/bin/python -m ichrisbirch.wsgi_scheduler
  environment:
    - ENVIRONMENT=testing
    # ... other config
```

**Prevention:** When overriding services in compose override files, ensure all required directives (build, image, etc.) are included.

### Incorrect Module Import Paths

**Problem:** Test runner fails with `ModuleNotFoundError` for test utility modules.

**Error Messages:**

```text
ImportError while loading conftest '/app/tests/conftest.py'.
tests/conftest.py:26: in <module>
    from tests.utils.environment import TestEnvironment
E   ModuleNotFoundError: No module named 'tests.utils.environment'
```

**Root Cause:** Import statement referenced wrong module path. The actual module was at `tests/environment.py`, not `tests/utils/environment.py`.

**Resolution:**

Fix the import path in `tests/conftest.py`:

```python
# Before (broken):
from tests.utils.environment import TestEnvironment

# After (working):
from tests.environment import TestEnvironment
```

**Prevention:**

- Use IDE auto-completion for imports
- Verify module structure before adding imports
- Add import validation to pre-commit hooks

### Docker Network Conflicts

**Problem:** Intermittent networking failures with "network not found" errors during test execution.

**Error Messages:**

```text
Error response from daemon: failed to set up container networking: network 29c640af9598b69b0e85acbdc4c59293e181060841e68af175b51c13cd045f79 not found
```

**Root Cause:** Orphaned Docker networks and containers from previous failed runs interfering with new test executions.

**Resolution:**

Comprehensive Docker cleanup:

```bash
# Stop all test containers
docker-compose -f docker-compose.yml -f docker-compose.test.yml down --remove-orphans

# Clean up containers, networks, and build cache
docker container prune -f
docker network prune -f
docker system prune -f  # Use with caution - removes unused images
```

**Prevention:**

- Always use `--remove-orphans` flag when stopping compose
- Regular cleanup of Docker resources
- Add cleanup commands to test scripts

### Complete Resolution Workflow

For comprehensive testing issues, follow this workflow:

1. **Clean Docker environment:**

```bash
docker-compose -f docker-compose.yml -f docker-compose.test.yml down -v --remove-orphans
docker network prune -f
```

1. **Verify and fix Dockerfile:**

```bash
# Check development stage includes test groups
grep -A 5 "uv sync" Dockerfile
# Should show: uv sync --frozen --group dev --group test
```

1. **Verify compose service definitions:**

```bash
# Check all services have build or image specified
docker-compose -f docker-compose.yml -f docker-compose.test.yml config
```

1. **Fix import paths:**

```bash
# Verify module exists
find tests/ -name "*.py" | grep -E "(environment|conftest)"
```

1. **Rebuild and test:**

```bash
docker-compose -f docker-compose.test.yml build --no-cache test-runner
ichrisbirch test
```

## Test Checklist

Before running tests, verify:

- [ ] Test database is running and accessible
- [ ] Schema exists and migrations are current
- [ ] Test dependencies are installed
- [ ] Environment variables are set correctly
- [ ] Test data fixtures are working
- [ ] Coverage configuration is correct
- [ ] Resource limits are appropriate for test load
