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

### Containers on Newer Networks Have No Internet (Dual iptables Backends)

**Problem:** Containers on one Docker network can reach their gateway but NOT the internet (ping `1.1.1.1` times out, `wget https://registry.npmjs.org` hangs). Containers on OTHER Docker networks on the same host work fine. DNS resolves correctly.

**Symptoms specific to this repo:** `icb-test-vue` can't finish `npm install` (times out fetching packages) while `icb-dev-vue` works. Testing containers show "health: starting" indefinitely.

**Cause (Arch Linux and similar):** The Linux kernel can have BOTH netfilter backends loaded simultaneously — `nftables` (modern) and `xt_tables` (legacy). Both evaluate packets at each netfilter hook. Docker writes MASQUERADE and FORWARD rules to its currently-configured backend (usually nft on modern systems), but if orphan rules exist in the OTHER backend referencing dead bridge IDs, they can drop traffic for newer Docker networks before nft's rules can NAT them.

How orphans appear: if Docker was ever briefly using `iptables-legacy` (an older install, a kernel update that temporarily broke `ip_tables` module loading, a failed daemon start), it wrote rules to legacy. When Docker switches to nft, it stops maintaining the legacy rules. Legacy rules persist until manually flushed, and the legacy kernel modules stay loaded for the session.

**Diagnostic:**

```bash
# Current backend — on Arch this should say iptables (nft-backed)
docker info | grep -i firewall

# Check both rule sets — stale bridge IDs in legacy are the signal
sudo iptables -t nat -L POSTROUTING -n -v        # Docker's current backend
sudo iptables-legacy -t nat -L POSTROUTING -n -v # orphan rules from prior backend

# Confirm legacy modules are loaded (can't evaluate legacy rules without them)
lsmod | grep -E "^(iptable|ip_tables)"

# Compare bridge IDs with actual Docker networks
docker network ls --no-trunc --format '{{.ID}} {{.Name}}'
```

**Recovery:**

```bash
sudo iptables-legacy -F
sudo iptables-legacy -t nat -F
sudo iptables-legacy -X
sudo iptables-legacy -t nat -X
sudo systemctl restart docker
./cli/icb testing rebuild --all --volumes
```

**Permanent prevention:** blacklist the legacy kernel modules so they never reload:

```bash
sudo tee /etc/modprobe.d/disable-iptables-legacy.conf <<'EOF'
blacklist iptable_filter
blacklist iptable_nat
blacklist iptable_raw
blacklist ip_tables
EOF
```

A reboot will ensure only `nftables` modules load.

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

### Root-Owned `node_modules/` on the Host (Expected, Not a Bug)

**Problem:** `./frontend/node_modules/` exists on the host as an empty directory owned by `root:root`, and you can't `npm install` into it as your user.

**Cause:** The Vue services mount `./frontend:/app` (bind mount) AND `vue_*_node_modules:/app/node_modules` (named volume) on top of it. For Docker to satisfy both mounts, the mount point `./frontend/node_modules/` must exist on the host side of the bind mount. If it doesn't, the Docker daemon auto-creates it — and because the daemon runs as root, that directory inherits root ownership. At runtime, the named volume shadows it, so container writes go to the volume, not the host directory. This is documented Docker behavior, not a bug in the project.

**Consequences:**

- Host-side `npm install` writes go to an empty, shadowed directory (invisible to the container)
- Pre-commit hooks that run `npm` on the host fail with EACCES unless the directory is pre-created by your user
- `git clean -fdx frontend/` requires sudo

**Resolution (pick based on goal):**

- **Accept the artifact** — if you only ever npm-install inside the container, nothing is broken. Leave the root-owned empty dir alone.
- **Pre-create as your user** — before starting containers, run `mkdir frontend/node_modules` so Docker finds it existing. Your host's node_modules content will seed the named volume on the next `down --volumes` + `up`, which may or may not be what you want.
- **Never edit compose files to "fix" the ownership** — there is no compose-level fix for this. The root-owned directory is a consequence of Docker's mount-point creation logic running as root.

### Container Crash Loop That Crashes `dockerd`

**Problem:** A container with `restart: unless-stopped` hits a deterministic error (e.g., npm install ENOTEMPTY from partial volume state), restart policy keeps retrying, eventually the daemon dies. `sudo systemctl status docker` may show `inactive (dead)` with `Job: ####` queued.

**Why it's self-inflicted:** Each restart involves creating and tearing down network namespaces, veth pairs, iptables rules, and DNS entries. At ~1 restart/second for extended periods, this can exhaust file descriptors, trigger kernel locking contention, or otherwise destabilize `dockerd`.

**Observed case (2026-04-16):** Vue test container stuck on `ENOTEMPTY: directory not empty, rename '/app/node_modules/data-urls' -> '/app/node_modules/.data-urls-CbOQj4xY'` — a partial npm install left `.data-urls-CbOQj4xY` temp directory non-empty, subsequent installs couldn't rename on top of it. `restartCount` climbed past 11 before dockerd died.

**Recovery:**

```bash
# 1. Bring docker back
sudo systemctl reset-failed docker.service docker.socket
sudo systemctl start docker

# 2. IMMEDIATELY kill the looping container (before restart policy puts docker back in the same loop)
docker rm -f icb-test-vue 2>/dev/null
docker volume rm icb-test-vue-node-modules 2>/dev/null

# 3. Clean rebuild
./cli/icb testing rebuild --all --volumes
```

**Prevention:** Consider `restart: on-failure:3` instead of `restart: unless-stopped` for dev-mode containers where a bad volume could trigger a crash loop. Caps retries at 3 so the daemon can't be DOS'd by a deterministic failure.

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
