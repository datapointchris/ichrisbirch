# Poetry to UV Migration Troubleshooting

This document chronicles the complete migration from Poetry to UV package management, including all issues encountered, solutions attempted, and the final working configuration.

## Background

The iChrisBirch project originally used Poetry for dependency management but encountered significant issues with Docker containerization, particularly with virtual environment handling and pytest execution in containerized environments.

!!! warning "Poetry Docker Incompatibility"
    Poetry's virtual environment copying between Docker stages is fundamentally broken in containerized environments, leading to missing executables and broken symlinks.

## Issue Timeline

### Initial Problem

**Error Encountered:**

```bash
docker-compose -f docker-compose.test.yml up test-runner
# Output: /app/.venv/bin/pytest: No such file or directory
```

**Root Cause Analysis:**
Poetry creates virtual environments with complex symlink structures that don't survive Docker's multi-stage build copying. The `.venv/bin/pytest` executable was missing despite Poetry claiming successful installation.

### Attempted Solutions (That Failed)

#### 1. Fix Poetry Docker Configuration

**What We Tried:**

```dockerfile
# Attempted fix in Dockerfile
ENV POETRY_VENV_IN_PROJECT=1
ENV POETRY_NO_INTERACTION=1
COPY --from=builder /app/.venv /app/.venv
```

**Why It Failed:**
Poetry's virtual environment structure with symlinks doesn't copy correctly between Docker layers. The symlinks become broken references.

#### 2. Manual Pytest Installation

**What We Tried:**

```dockerfile
RUN .venv/bin/pip install pytest pytest-cov
```

**Why It Failed:**
The `.venv/bin/pip` itself was a broken symlink, creating a circular dependency problem.

#### 3. Poetry Path Modifications

**What We Tried:**

```dockerfile
ENV PATH="/app/.venv/bin:$PATH"
RUN which pytest  # Still not found
```

**Why It Failed:**
Setting PATH doesn't fix broken symlinks; the underlying executable files were never properly copied.

## Final Resolution: Complete Migration to UV

### Why UV Was Chosen

1. **Better Docker Support**: UV handles containerized environments correctly
2. **Faster Installation**: UV is significantly faster than Poetry
3. **PEP 621 Compliance**: Uses modern Python packaging standards
4. **Simplified Dependencies**: Cleaner dependency group management

### Migration Steps

#### 1. Convert pyproject.toml

**Before (Poetry format):**

```toml
[tool.poetry]
name = "ichrisbirch"
version = "0.1.0"

[tool.poetry.dependencies]
python = "^3.12"
fastapi = "^0.104.1"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"
```

**After (UV/PEP 621 format):**

```toml
[project]
name = "ichrisbirch"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.104.1",
]

[dependency-groups]
dev = [
    "pytest>=7.4.3",
]
test = [
    "pytest>=7.4.3",
    "pytest-cov>=4.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

#### 2. Update Dockerfile

**Before (Poetry):**

```dockerfile
FROM python:3.12-slim as builder
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry config venv.in-project true && poetry install --no-root
```

**After (UV):**

```dockerfile
FROM python:3.12-slim as builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

FROM builder as development
COPY . .
RUN uv sync --frozen --group dev --group test
```

#### 3. Update Docker Compose

**Before (Poetry):**

```yaml
test-runner:
  build:
    target: development
  command: ["poetry", "run", "pytest", "-vv", "--cov=ichrisbirch"]
```

**After (UV):**

```yaml
test-runner:
  build:
    target: development
  command: ["uv", "run", "pytest", "-vv", "--cov=ichrisbirch"]
```

#### 4. Update CI/CD Workflows

**Before (Poetry):**

```yaml
- name: Install Poetry
  run: pip install poetry
- name: Install dependencies
  run: poetry install
- name: Run tests
  run: poetry run pytest
```

**After (UV):**

```yaml
- name: Install UV
  run: pip install uv
- name: Install dependencies
  run: uv sync --frozen --group dev --group test
- name: Run tests
  run: uv run pytest
```

## Additional Issues Resolved

### Database Schema Creation

**Issue:** Tests failing because database schema wasn't created in test environment.

**Root Cause:** `POSTGRES_DB_SCHEMA` environment variable missing from test configuration.

**Solution:**

```yaml
# docker-compose.test.yml
services:
  test-runner:
    environment:
      - POSTGRES_DB_SCHEMA=ichrisbirch_test
```

### Package Source Code Access

**Issue:** UV couldn't access package source code for local development.

**Solution:** Ensure source code is copied before `uv sync`:

```dockerfile
FROM builder as development
COPY . .  # Copy source before sync
RUN uv sync --frozen --group dev --group test
```

## Verification Steps

After migration, verify everything works:

```bash
# 1. Check UV installation
docker-compose -f docker-compose.test.yml build

# 2. Verify pytest is available
docker-compose -f docker-compose.test.yml run test-runner uv run which pytest

# 3. Run actual tests
docker-compose -f docker-compose.test.yml up test-runner

# 4. Check test database connection
docker-compose -f docker-compose.test.yml run test-runner uv run python -c "
from ichrisbirch.config import settings
print(f'Database URL: {settings.database_url}')
"
```

## Benefits Achieved

1. **Working Tests**: Docker test environment now functions correctly
2. **Faster Builds**: UV installation is significantly faster than Poetry
3. **Simpler Configuration**: Fewer environment variables and cleaner setup
4. **Better CI/CD**: More reliable GitHub Actions workflows
5. **Future-Proof**: Using modern PEP 621 standards

## Prevention

To avoid similar issues in the future:

1. **Test Docker Builds Regularly**: Don't let Docker configurations drift
2. **Use UV for New Projects**: UV has better containerization support
3. **Validate Multi-Stage Builds**: Ensure all stages have required executables
4. **Monitor Dependency Management**: Keep dependency management tools updated
5. **Document Environment Variables**: All required variables must be documented

!!! tip "Migration Checklist"
    When migrating package managers:

    - [ ] Convert pyproject.toml format
    - [ ] Update all Dockerfiles
    - [ ] Modify Docker Compose files
    - [ ] Update CI/CD workflows
    - [ ] Update deployment scripts
    - [ ] Test all environments (dev, test, prod)
    - [ ] Update documentation
