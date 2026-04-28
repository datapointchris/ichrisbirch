# Docker Compose Architecture

This document details how Docker Compose orchestrates the ichrisbirch application services across different environments.

## Overview

The ichrisbirch application uses a **layered Docker Compose approach** where environment-specific override files customize the base configuration for each deployment context.

## Environment Comparison

| Aspect | Development | Testing | CI | Production |
| --- | --- | --- | --- | --- |
| **Purpose** | Local development with hot reload | Running pytest suite | GitHub Actions CI | Live deployment |
| **Compose Files** | base + dev | base + test | base + test + ci | base only |
| **External Ports** | Standard (8000, 5432) | Alternate (8001, 5434, 8443) | Alternate (same as test) | Standard |
| **Hot Reload** | Yes | No | No | No |
| **AWS Credentials** | `~/.config/aws` mount | `~/.config/aws` mount | Environment variables (OIDC) | IAM role |
| **Database** | Persistent volume | tmpfs (in-memory) | tmpfs (in-memory) | Persistent volume |
| **Traefik** | Dashboard enabled | Dashboard enabled | Dashboard disabled | Dashboard disabled |
| **Network** | `icb-dev-proxy` | `icb-test-proxy` | Internal bridge | External `proxy` |

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
| --- | --- | --- |
| `traefik` | Reverse proxy with HTTPS | 80, 443, 8080 |
| `postgres` | PostgreSQL 16 database | 5432 |
| `redis` | Redis 7 cache | 6379 |
| `api` | FastAPI backend | 8000 |
| `vue` | Vue 3 frontend (SPA) | 5173 (dev) / 80 (prod via Caddy) |
| `chat` | Streamlit chat interface | 8505 |
| `scheduler` | APScheduler background jobs | N/A |
| `mcp` | MCP server (FastMCP streamable HTTP) | 3000 |

### Service Dependencies

```text
postgres ─────┬───► api ──────► vue (Vue 3 SPA)
              │       │
redis ────────┤       ├──────► chat
              │       │
              │       ├──────► mcp
              │       │
              └───────┴──────► scheduler
```

### Routing

All routing is handled by the Traefik file provider (`deploy-containers/traefik/dynamic/{env}/routing.yml`), not Docker labels. Vue path prefixes are generated from `deploy-containers/traefik/vue-paths.txt` via `ich routing generate`.

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

### Bind Mount + Named Volume Overlap (Vue services)

The vue service in dev and test uses a mount pattern that deserves explicit callout:

```yaml
volumes:
  - ./frontend:/app                          # bind mount: host source → container
  - vue_node_modules:/app/node_modules       # named volume on top of /app/node_modules
```

**Why:** Mounting `./frontend:/app` would expose the host's empty (or stale) `node_modules/` to the container. The named volume overlays that subpath so npm packages installed inside the container go to Docker-managed storage, not the host's filesystem. This keeps install fast (Linux ext4 vs slow fsnotify on bind mounts), avoids permission conflicts, and isolates container-side node_modules from IDE/pre-commit hooks that might write there.

**Side effect — root-owned host mount point:** When Docker starts a container with this config, it needs `./frontend/node_modules/` to exist on the host as a mount point. If it doesn't, the Docker daemon auto-creates it, and because the daemon runs as `root`, the directory inherits `root:root` ownership. This is documented Docker behavior. At runtime the named volume shadows it and container writes go to the volume — the empty host dir is just an anchor.

**Practical implications:**

- Your host's `frontend/node_modules/` may appear empty even after `npm install` ran in the container.
- Running `npm install` on the host writes to a root-owned dir and usually fails with EACCES. Pre-create as your user (`mkdir frontend/node_modules`) before bringing up containers if you need host-side installs.
- Nothing in `docker-compose.*.yml` can change this — it's Linux mount semantics.

**Recovery for corrupted volumes:** Partial install state in the named volume (e.g., npm install interrupted mid-run) can cause persistent ENOTEMPTY errors. Use `./cli/icb testing rebuild --all --volumes` (or `dev rebuild --all --volumes`) to wipe the named volume and start fresh. See [Docker troubleshooting](../troubleshooting/docker-issues.md#container-crash-loop-that-crashes-dockerd) for the full crash-loop recovery procedure.

### Usage

```bash
# Via CLI (recommended)
./cli/icb dev start

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
| --- | --- | --- |
| API | 8000 | 8001 |
| Vue | 5173 | 5174 |
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
./cli/icb test run

# Keep containers for debugging
./cli/icb test run --keep

# Manual management (for extended debugging)
./cli/icb testing start
uv run pytest
./cli/icb testing stop

# Direct Docker Compose
docker compose -f docker-compose.yml -f docker-compose.test.yml \
  --project-name icb-test up -d
```

## CI Override (`docker-compose.ci.yml`)

**Purpose:** Run tests in GitHub Actions where local paths don't exist.

### Why CI Needs Special Handling

The CI environment differs from local development:

| Difference | Local | CI | Solution |
| --- | --- | --- | --- |
| AWS credentials | `~/.config/aws` exists | Only env vars via OIDC | Remove bind mount |
| Proxy network | Pre-created externally | Doesn't exist | Create as bridge |
| Project files | Full local checkout | GitHub checkout only | Use volumes not binds |
| Traefik dashboard | Useful for debugging | Not needed | Disable |

### CI-Specific Overrides

```yaml
services:
  api:
    # !override replaces the base list so the docker.sock bind mount from
    # test.yml is NOT merged in. The anonymous /app/.venv volume matches
    # the test.yml pattern — DO NOT reintroduce a named venv/uv-cache volume,
    # since persistent named volumes caused stale-venv test hangs.
    volumes: !override
      - .:/app
      - /app/.venv
      - ichrisbirch_logs:/var/log/ichrisbirch

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
                              ├──► app.domain.com + PathPrefixes ──► Vue (:5173)
                              └──► chat.domain.com ──► Chat (:8505)
```

### Internal Communication

Services communicate via Docker DNS using service names:

```python
# Scheduler connecting to Postgres
engine = create_engine('postgresql://postgres:5432/ichrisbirch')
```

## Common Operations

### Starting Environments

```bash
# Development
./cli/icb dev start

# Testing
./cli/icb testing start

# Production
./cli/icb prod start
```

### Viewing Logs

```bash
# All services
./cli/icb dev logs

# Specific service
docker compose logs -f api

# With timestamps
docker compose logs -f --timestamps api
```

### Rebuilding Images

```bash
# Rebuild and restart
./cli/icb dev rebuild

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
docker inspect icb-dev-api
```

### Port Conflicts

If ports are in use:

```bash
# Find what's using the port
lsof -i :8000

# Use testing ports instead
./cli/icb testing start  # Uses 8001, 5001, etc.
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

1. **Use the CLI:** `./cli/icb dev start` handles complexity
2. **Don't mix environments:** Use testing ports when dev is running
3. **Check health first:** `./cli/icb dev health` before debugging
4. **Read logs:** Most issues are visible in container logs
5. **Rebuild after Dockerfile changes:** Images don't auto-update
