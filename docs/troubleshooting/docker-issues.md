# Docker Configuration Troubleshooting

This document covers common Docker-related issues encountered during development and deployment of the iChrisBirch project, including build failures, networking problems, and container orchestration issues.

## Multi-Stage Build Issues

### Missing Executables in Container Stages

**Problem:** Files copied from previous stages don't work or are missing.

**Symptoms:**

- `/app/.venv/bin/pytest: No such file or directory`
- Commands work in builder stage but fail in runtime stage
- Broken symlinks after `COPY --from=builder`

**Root Cause:** Package managers like Poetry create complex directory structures with symlinks that don't survive Docker layer copying.

**Resolution:**
Use UV instead of Poetry for better Docker compatibility:

```dockerfile
# Good: UV creates self-contained installations
FROM python:3.12-slim as builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

FROM builder as development
COPY . .
RUN uv sync --frozen --group dev --group test
```

**Prevention:**

- Test each stage individually: `docker build --target=development .`
- Verify executables exist: `docker run --rm image which pytest`
- Use package managers designed for containers

## Container Networking Issues

### Service Communication Failures

**Problem:** Services can't communicate with each other in Docker Compose.

**Symptoms:**

- `Connection refused` errors between services
- Services start but can't reach database/API
- Works locally but fails in containers

**Common Causes:**

1. **Wrong hostname:** Using `localhost` instead of service name
1. **Port mapping confusion:** Mixing internal and external ports
1. **Network isolation:** Services on different networks

**Resolution:**

```yaml
# docker-compose.yml
services:
  app:
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/db
      # Use service name 'postgres', not 'localhost'
    networks:
      - app-network

  postgres:
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

**Debugging Steps:**

```bash
# Check service connectivity
docker-compose exec app ping postgres

# Verify environment variables
docker-compose exec app env | grep DATABASE

# Check port availability
docker-compose exec app nc -zv postgres 5432
```

## Build Context and Performance

### Large Build Contexts

**Problem:** Docker builds are slow due to large context.

**Symptoms:**

- `Sending build context to Docker daemon` takes minutes
- Builds timeout or run out of space
- Unnecessary files in containers

**Resolution:**

Create comprehensive `.dockerignore`:

```dockerignore
# Version control
.git/
.gitignore

# Python
__pycache__/
*.pyc
.pytest_cache/

# Development
.vscode/
*.log
node_modules/

# Documentation
docs/
*.md

# CI/CD
.github/

# Local development
.env.local
docker-compose.override.yml
```

**Performance Tips:**

- Put frequently changing files (source code) after stable dependencies
- Use multi-stage builds to separate build dependencies from runtime
- Cache dependency installation layers

### Layer Caching Issues

**Problem:** Dependencies reinstall on every build despite no changes.

**Common Mistake:**

```dockerfile
# Bad: Any file change invalidates dependency cache
COPY . .
RUN uv sync --frozen
```

**Correct Approach:**

```dockerfile
# Good: Cache dependencies separately
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Source code in separate layer
COPY . .
RUN uv sync --frozen --group dev
```

## Environment Variable Management

### Missing Environment Variables

**Problem:** Services fail to start with configuration errors.

**Symptoms:**

- Services exit immediately after starting
- "Environment variable not set" errors
- Database connection failures

**Resolution:**

1. **Use environment files:**

```yaml
# docker-compose.yml
services:
  app:
    env_file:
      - .env
      - .env.local  # Optional overrides
```

1. **Provide defaults:**

```yaml
services:
  app:
    environment:
      - POSTGRES_DB=${POSTGRES_DB:-ichrisbirch}
      - DEBUG=${DEBUG:-false}
```

1. **Validate environment:**

```python
# In your application startup
from ichrisbirch.config import settings

# Let it fail fast if misconfigured
assert settings.database_url, "DATABASE_URL must be set"
```

## Volume and Persistence Issues

### Database Data Loss

**Problem:** Database data disappears when containers restart.

**Cause:** No persistent volume configured for database.

**Resolution:**

```yaml
services:
  postgres:
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
    driver: local
```

### File Permission Problems

**Problem:** Files created in containers have wrong ownership.

**Symptoms:**

- Permission denied when accessing files from host
- Files owned by root instead of user
- Build failures due to permission issues

**Resolution:**

```dockerfile
# Match host user ID in development
ARG UID=1000
ARG GID=1000
RUN groupadd -g $GID appgroup && \
    useradd -u $UID -g $GID -m appuser
USER appuser
```

Or in docker-compose for development:

```yaml
services:
  app:
    user: "${UID:-1000}:${GID:-1000}"
```

## Service Orchestration Issues

### Service Startup Order

**Problem:** Services start before dependencies are ready.

**Symptoms:**

- Application fails to connect to database during startup
- Race conditions in service initialization
- Containers restart repeatedly

**Resolution:**

Use `depends_on` with health checks:

```yaml
services:
  app:
    depends_on:
      postgres:
        condition: service_healthy

  postgres:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
```

### Resource Constraints

**Problem:** Services crash due to insufficient resources.

**Resolution:**

Set resource limits:

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

## Debugging Techniques

### Container Inspection

```bash
# Check running containers
docker-compose ps

# View logs
docker-compose logs app
docker-compose logs -f --tail=100 app

# Execute commands in container
docker-compose exec app bash
docker-compose exec app uv run python -c "import sys; print(sys.path)"

# Inspect container configuration
docker inspect $(docker-compose ps -q app)
```

### Network Debugging

```bash
# List networks
docker network ls

# Inspect network configuration
docker network inspect ichrisbirch_default

# Test connectivity between services
docker-compose exec app ping postgres
docker-compose exec app nc -zv postgres 5432
```

### Build Debugging

```bash
# Build with verbose output
docker-compose build --progress=plain --no-cache

# Build specific stage
docker build --target=development .

# Inspect intermediate stages
docker build --rm=false .
docker run -it <intermediate-id> bash
```

## Common Error Messages

### "No such file or directory"

**Error:** `/app/.venv/bin/pytest: No such file or directory`

**Cause:** Broken symlinks in virtual environment after Docker layer copy.

**Fix:** Use UV instead of Poetry, ensure proper multi-stage build.

### "Connection refused"

**Error:** `psycopg2.OperationalError: connection to server at "localhost" (127.0.0.1) port 5432 refused`

**Cause:** Using `localhost` instead of Docker service name.

**Fix:** Update connection string to use service name: `postgres:5432`

### "Port already in use"

**Error:** `Error starting userland proxy: listen tcp 0.0.0.0:5432: bind: address already in use`

**Cause:** Port conflict with host system or another container.

**Fix:** Change external port mapping or stop conflicting service.

## Prevention Checklist

- [ ] Use `.dockerignore` to exclude unnecessary files
- [ ] Test each Docker stage individually
- [ ] Use service names for inter-service communication
- [ ] Configure health checks for critical services
- [ ] Set up persistent volumes for data
- [ ] Document required environment variables
- [ ] Test builds on clean systems (CI/CD)
- [ ] Monitor resource usage and set limits
