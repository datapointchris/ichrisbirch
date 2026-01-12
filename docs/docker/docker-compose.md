# Docker Compose Architecture

This document details how Docker Compose orchestrates the ichrisbirch application services across different environments.

## Overview

The ichrisbirch application uses a **layered Docker Compose approach** where environment-specific override files customize the base configuration for each deployment context.

## Environment Comparison

| Aspect | Development | Testing | CI | Production |
|--------|-------------|---------|-----|------------|
| **Purpose** | Local development with hot reload | Running pytest suite | GitHub Actions CI | Live deployment |
| **Compose Files** | base + dev | base + test | base + test + ci | base only |
| **External Ports** | Standard (8000, 5000, 5432) | Alternate (8001, 5001, 5434) | Alternate (same as test) | Standard |
| **Hot Reload** | Yes | No | No | No |
| **AWS Credentials** | `~/.config/aws` mount | `~/.config/aws` mount | Environment variables (OIDC) | IAM role |
| **Database** | Persistent volume | tmpfs (in-memory) | tmpfs (in-memory) | Persistent volume |
| **Traefik** | Dashboard enabled | Dashboard enabled | Dashboard disabled | Dashboard disabled |
| **Network** | External `proxy` | External `proxy` | Internal bridge | External `proxy` |

## File Structure

```text
docker-compose.yml           # Base/production configuration
docker-compose.dev.yml       # Development overrides (hot reload, mounts)
docker-compose.test.yml      # Testing overrides (alternate ports, tmpfs)
docker-compose.ci.yml        # CI overrides (no local mounts, internal network)
```

## How Layering Works

Docker Compose merges multiple files in order, with later files overriding earlier ones:

```bash
# Development
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Testing (local)
docker compose -f docker-compose.yml -f docker-compose.test.yml up -d

# CI (GitHub Actions)
docker compose -f docker-compose.yml -f docker-compose.test.yml -f docker-compose.ci.yml up -d

# Production
docker compose -f docker-compose.yml up -d
```

### Layering Example

**Base (`docker-compose.yml`):**

```yaml
services:
  api:
    build:
      target: production
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

**Dev Override (`docker-compose.dev.yml`):**

```yaml
services:
  api:
    build:
      target: development
    volumes:
      - .:/app  # Adds source mount for hot reload
      - ~/.config/aws:/root/.aws:ro  # AWS credentials
```

**Result:** Dev environment gets development build target AND source mounts.

## Base Configuration (`docker-compose.yml`)

The base file defines production-ready services:

### Core Services

| Service | Purpose | Internal Port |
|---------|---------|---------------|
| `traefik` | Reverse proxy with HTTPS | 80, 443, 8080 |
| `postgres` | PostgreSQL 16 database | 5432 |
| `redis` | Redis 7 cache | 6379 |
| `api` | FastAPI backend | 8000 |
| `app` | Flask frontend | 5000 |
| `chat` | Streamlit chat interface | 8505 |
| `scheduler` | APScheduler background jobs | N/A |

### Service Dependencies

```text
postgres ─────┬───► api ──────► app
              │       │
redis ────────┤       ├──────► chat
              │       │
              └───────┴──────► scheduler
```

Services wait for dependencies via health checks:

```yaml
depends_on:
  postgres:
    condition: service_healthy
  redis:
    condition: service_healthy
```

## Development Override (`docker-compose.dev.yml`)

**Purpose:** Enable rapid development with hot reload and debugging.

### Development Features

- **Hot reload:** Source code mounted as volume, servers watch for changes
- **Debug logging:** Verbose log output
- **Local credentials:** AWS credentials mounted from host
- **Traefik dashboard:** Enabled for debugging routing

### Volume Mounts

```yaml
volumes:
  - type: bind
    source: .
    target: /app
  - type: bind
    source: ~/.config/aws
    target: /root/.aws
    read_only: true
```

### Usage

```bash
# Via CLI (recommended)
./cli/ichrisbirch dev start

# Direct Docker Compose
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

## Testing Override (`docker-compose.test.yml`)

**Purpose:** Run pytest suite with isolated, fast database.

### Testing Features

- **Alternate ports:** Avoids conflicts with running dev environment
- **tmpfs database:** In-memory PostgreSQL for speed
- **No persistence:** Each test run starts fresh
- **Optimized Postgres:** Disabled fsync/durability for performance

### Port Mapping

| Service | Dev Port | Test Port |
|---------|----------|-----------|
| API | 8000 | 8001 |
| App | 5000 | 5001 |
| Chat | 8505 | 8507 |
| PostgreSQL | 5432 | 5434 |
| Redis | 6379 | 6380 |
| Traefik HTTPS | 443 | 8443 |

### Database Optimizations

```yaml
postgres:
  tmpfs:
    - /tmp/postgres  # In-memory storage
  command: >
    postgres
    -c fsync=off
    -c synchronous_commit=off
    -c full_page_writes=off
```

### Testing Usage

```bash
# Recommended: Ephemeral test run (starts fresh, runs tests, stops)
./cli/ichrisbirch test run

# With coverage
./cli/ichrisbirch test cov

# Keep containers for debugging
./cli/ichrisbirch test run --keep

# Manual management (for extended debugging)
./cli/ichrisbirch testing start
uv run pytest
./cli/ichrisbirch testing stop

# Direct Docker Compose
docker compose -f docker-compose.yml -f docker-compose.test.yml \
  --project-name ichrisbirch-test up -d
```

## CI Override (`docker-compose.ci.yml`)

**Purpose:** Run tests in GitHub Actions where local paths don't exist.

### Why CI Needs Special Handling

The CI environment differs from local development:

| Difference | Local | CI | Solution |
|------------|-------|-----|----------|
| AWS credentials | `~/.config/aws` exists | Only env vars via OIDC | Remove bind mount |
| Proxy network | Pre-created externally | Doesn't exist | Create as bridge |
| Project files | Full local checkout | GitHub checkout only | Use volumes not binds |
| Traefik dashboard | Useful for debugging | Not needed | Disable |

### CI-Specific Overrides

```yaml
services:
  api:
    volumes:
      # Remove AWS credentials mount, keep other volumes
      - type: bind
        source: .
        target: /app
      - type: volume
        source: venv_shared
        target: /app/.venv

networks:
  proxy:
    external: false  # Create internally instead of expecting external
    driver: bridge
```

### Container Startup in CI

The CI workflow pre-starts containers before pytest runs:

```yaml
# Phase 1: Database services
docker compose ... up -d --build postgres redis
sleep 10

# Phase 2: Application services
docker compose ... up -d --build api app chat scheduler
sleep 30
```

**Why this order:**

1. `postgres` and `redis` must pass health checks first
2. `api` initializes the shared virtual environment
3. `scheduler` creates `apscheduler_jobs` table
4. Sleep allows health checks to complete

### Test Environment Detection

The test fixtures detect CI and skip container management:

```python
# In tests/environment.py
@property
def is_ci(self) -> bool:
    return os.environ.get('CI', '').lower() == 'true'

def setup(self):
    if self.is_ci:
        # Containers pre-started by workflow
        logger.info('Running in CI - containers should be pre-started')
    else:
        # Start containers ourselves
        self.setup_test_services()
```

## Production Configuration

**Purpose:** Production deployment with security and reliability.

### Production Features

- **No source mounts:** Code baked into image
- **Non-root user:** Security hardening
- **Gunicorn workers:** Multi-process for performance
- **Resource limits:** Prevent runaway containers
- **Health checks:** Automatic recovery

### Production Differences

```yaml
services:
  api:
    build:
      target: production  # Minimal image, no dev deps
    user: appuser  # Non-root
    volumes: []  # No source mounts
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
```

## Network Architecture

### Traefik Routing

All HTTP(S) traffic flows through Traefik:

```text
Internet ──► Traefik (:443) ──┬──► api.domain.com ──► API (:8000)
                              ├──► app.domain.com ──► App (:5000)
                              └──► chat.domain.com ──► Chat (:8505)
```

### Internal Communication

Services communicate via Docker DNS using service names:

```python
# Flask app calling FastAPI
response = httpx.get('http://api:8000/tasks/')

# Scheduler connecting to Postgres
engine = create_engine('postgresql://postgres:5432/ichrisbirch')
```

## Common Operations

### Starting Environments

```bash
# Development
./cli/ichrisbirch dev start

# Testing
./cli/ichrisbirch testing start

# Production
./cli/ichrisbirch prod start
```

### Viewing Logs

```bash
# All services
./cli/ichrisbirch dev logs

# Specific service
docker compose logs -f api

# With timestamps
docker compose logs -f --timestamps api
```

### Rebuilding Images

```bash
# Rebuild and restart
./cli/ichrisbirch dev rebuild

# Rebuild specific service
docker compose build api
docker compose up -d api
```

### Accessing Containers

```bash
# Shell into running container
docker compose exec api bash

# Run one-off command
docker compose run --rm api python -c "print('hello')"
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose logs api

# Check health
docker compose ps

# Inspect container
docker inspect ichrisbirch-api-dev
```

### Port Conflicts

If ports are in use:

```bash
# Find what's using the port
lsof -i :8000

# Use testing ports instead
./cli/ichrisbirch testing start  # Uses 8001, 5001, etc.
```

### Database Connection Issues

```bash
# Check postgres is healthy
docker compose ps postgres

# Test connection
docker compose exec postgres psql -U postgres -d ichrisbirch -c "SELECT 1"

# Check logs
docker compose logs postgres
```

### Network Issues

```bash
# List networks
docker network ls

# Inspect network
docker network inspect ichrisbirch_proxy

# Recreate network
docker network rm ichrisbirch_proxy
docker network create proxy
```

## Best Practices

1. **Use the CLI:** `./cli/ichrisbirch dev start` handles complexity
2. **Don't mix environments:** Use testing ports when dev is running
3. **Check health first:** `./cli/ichrisbirch dev health` before debugging
4. **Read logs:** Most issues are visible in container logs
5. **Rebuild after Dockerfile changes:** Images don't auto-update
