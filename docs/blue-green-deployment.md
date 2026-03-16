# Blue/Green Deployment

This document covers the zero-downtime deployment strategy for ichrisbirch production.

## Why Blue/Green

The previous deployment approach ran `docker compose down` before building new images. If the build failed (OOM, network error, disk space), the site went down with zero containers running. Blue/green deployment solves this by keeping old containers serving traffic until new ones are fully verified.

## How It Works

Two parallel sets of **app containers** exist — called **blue** and **green**. Infrastructure services (Traefik, PostgreSQL, Redis) are separate and always running. One color is "live" (serving traffic), the other is "standby."

```text
                   ┌─────────────────────────────────────────────────┐
                   │              icb-infra (always running)         │
Internet           │                                                 │
  → Cloudflare     │   Traefik ──→ routing.yml ──→ icb-blue-api     │
    → Tunnel       │     :80          (file         icb-blue-vue     │
      → :80        │                  provider)     icb-blue-app     │
                   │   PostgreSQL                   icb-blue-chat    │
                   │   Redis                                         │
                   │                                                 │
                   │              icb-green (standby, not receiving  │
                   │                         traffic until verified) │
                   └─────────────────────────────────────────────────┘
```

The deploy cycle:

1. Build new images and start the standby color
2. Wait for Docker health checks to pass
3. Run full smoke tests (32 endpoints) against the standby containers
4. Switch Traefik routing by rewriting `routing.yml` (picked up in 1-2 seconds)
5. Grace period, then tear down old color

If anything fails in steps 1-3, the live color is untouched. Zero downtime, zero risk.

## Architecture

### Compose File Split

| File | Project Name | Contains | Lifecycle |
|------|-------------|----------|-----------|
| `docker-compose.infra.yml` | `icb-infra` | Traefik, PostgreSQL, Redis | Always running, never restarted during deploys |
| `docker-compose.app.yml` | `icb-blue` or `icb-green` | API, App, Vue, Chat, Scheduler | Created/destroyed per deploy |
| `docker-compose.yml` | `icb-prod` | All services (legacy) | Emergency fallback only |

Dev and test environments (`docker-compose.dev.yml`, `docker-compose.test.yml`) are completely unaffected.

### Networking

All containers join the external `proxy` network. Traefik resolves app containers by Docker DNS name (e.g., `http://icb-blue-api:8000`). App containers also join `icb-infra_default` to reach PostgreSQL and Redis by service name.

App services have `ports: []` — they do **not** bind to host ports. Only Traefik binds `:80`. This means two copies of the API both listening on container port 8000 is fine — they have separate network IPs. No port collisions.

### Traefik Routing

App containers set `traefik.enable=false`. All production routing is defined in a file provider config:

**`deploy-containers/traefik/dynamic/prod/routing.yml`**

This file defines all routers (api, api-proxy, vue-paths, app, chat) and services pointing to the active color's containers. Switching traffic means rewriting 4 URLs in this file:

```yaml
# The only lines that change per deploy:
services:
  api:
    loadBalancer:
      servers:
        - url: "http://icb-blue-api:8000"    # ← blue or green
  vue:
    loadBalancer:
      servers:
        - url: "http://icb-blue-vue:80"
  app:
    loadBalancer:
      servers:
        - url: "http://icb-blue-app:5000"
  chat:
    loadBalancer:
      servers:
        - url: "http://icb-blue-chat:8505"
```

Traefik has `--providers.file.watch=true`, so it hot-reloads within 1-2 seconds of the file changing. No restart needed.

### State Tracking

| File | Location | Purpose |
|------|----------|---------|
| `bluegreen-state` | `/var/lib/ichrisbirch/bluegreen-state` | Active color (`blue` or `green`) |
| Deploy lock | `/var/lock/ichrisbirch-deploy.lock` | Prevents concurrent deploys |

Both are outside the git repo to avoid `git pull` conflicts.

## Deploy Flow

The deploy script at `scripts/deploy-homelab.sh` runs this sequence:

```text
 0. acquire_lock()              # mkdir-based lock, exit if another deploy running
 1. check_prerequisites()
 2. pull_latest_code()
 3. decrypt_secrets()
 4. determine_colors()          # Read bluegreen-state → LIVE=blue, DEPLOY=green
 5. ensure_infra_running()      # Start icb-infra if not already up
 6. build_new_images()          # Build DEPLOY color images (site stays up on LIVE)
 7. start_new_containers()      # docker compose up -d for DEPLOY color
 8. wait_for_healthy()          # Poll Docker healthchecks on DEPLOY containers (90s)
 9. run_migrations()            # alembic upgrade head on DEPLOY API container
10. run_smoke_tests()           # Full 32-endpoint smoke suite on DEPLOY containers
11. switch_traffic()            # Rewrite routing.yml → DEPLOY color, atomic mv
12. update_state()              # Write DEPLOY color to bluegreen-state
13. grace_period()              # Wait 30s (manual rollback window)
14. stop_old_containers()       # docker compose down for LIVE color
15. cleanup_docker()            # Prune old images
16. notify_slack()
```

If steps 6-10 fail, the LIVE containers keep serving traffic. The deploy script cleans up the failed DEPLOY containers, sends a Slack failure notification, and exits non-zero.

### Smoke Test Validation

Before switching traffic, the deploy script runs the full smoke test suite against the new containers:

```bash
# Calls the existing /admin/smoke-tests/ endpoint on the new API container
docker exec icb-${DEPLOY_COLOR}-api curl -sf \
    -X POST http://localhost:8000/admin/smoke-tests/ \
    -H "Remote-User: admin@ichrisbirch.com" \
    -H "Remote-Email: admin@ichrisbirch.com" \
    | jq -e '.all_critical_passed == true'
```

This tests 32 GET endpoints across critical, important, and secondary tiers. The deploy only proceeds if `all_critical_passed` is true. Vue and Flask containers are also health-checked directly.

### Concurrent Deploy Protection

A lock file prevents two deploys from running simultaneously:

```bash
LOCK_FILE="/var/lock/ichrisbirch-deploy.lock"
if ! mkdir "$LOCK_FILE" 2>/dev/null; then
    exit 0  # Another deploy is handling it
fi
```

`mkdir` is atomic on Linux. The second deploy exits harmlessly. The running deploy already has the latest code from `git pull`.

## CLI Commands

### Blue/Green Commands

```bash
icb prod deploy-status    # Show active color, container status, routing state
icb prod rollback         # Switch traffic back to previous color
```

### Standard Commands (Blue/Green Aware)

These commands automatically detect whether blue/green is active and act accordingly:

```bash
icb prod start            # Start infra + active color (or legacy single-compose)
icb prod stop             # Stop active color + infra (or legacy)
icb prod restart          # Restart active color + infra (or legacy)
icb prod status           # Show infra + active color status (or legacy)
icb prod logs [service]   # View active color logs (or legacy)
icb prod health           # Health check with correct container names
icb prod smoke            # Run smoke tests via API
```

### Emergency Fallback

If blue/green causes issues, the original `docker-compose.yml` still works:

```bash
icb prod legacy-rebuild   # Old-style down→build→up (causes downtime)
```

## Database Migrations

Blue/green with a shared database requires **backward-compatible migrations**. Both old code and new code must work with the new schema during the brief overlap.

### Safe Operations (Single Deploy)

- Add a nullable column
- Add a new table
- Add an index
- Backfill data in existing columns

### Unsafe Operations (Two-Phase Deploy)

These require two separate deploys:

| Operation | Phase 1 | Phase 2 |
|-----------|---------|---------|
| Make column NOT NULL | Backfill NULLs + update code to always set value | Add NOT NULL constraint |
| Rename column | Add new column + backfill + update code to use new | Drop old column |
| Drop column | Remove all code references | Drop column from schema |
| Change column type | Add new column with new type + backfill | Drop old column |

### Example: Adding NOT NULL Constraint

Column `tasks.category` has NULLs, you want NOT NULL with default `"general"`.

**Deploy 1** — backfill + update code:

```python
# Migration
def upgrade():
    op.execute("UPDATE tasks SET category = 'general' WHERE category IS NULL")

# Code change: schema now always provides a value
category: str = "general"  # was: category: str | None = None
```

**Deploy 2** — add constraint:

```python
def upgrade():
    op.execute("UPDATE tasks SET category = 'general' WHERE category IS NULL")
    op.alter_column('tasks', 'category', nullable=False, server_default='general')
```

## Rollback

### Automatic (Pre-Switch Failure)

If the build, health checks, or smoke tests fail, the live containers were never touched. The deploy script stops the failed containers and exits. No action needed.

### Manual (Post-Switch Problem)

```bash
icb prod rollback
```

This command:

1. Reads `bluegreen-state` to find the current color
2. Determines the previous color
3. Checks if previous containers are still running (within grace period) or restarts them
4. Rewrites `routing.yml` to point to the previous color
5. Updates `bluegreen-state`

Traefik picks up the routing change within 1-2 seconds.

### Rollback Window

After switching traffic, the deploy script waits 30 seconds before tearing down old containers. During this window, the old containers are still running and rollback is instant (just a file write). After the grace period, rollback requires restarting the old containers (adds ~30-60 seconds).

## Infrastructure Updates

Traefik, PostgreSQL, and Redis run in `icb-infra` and are **not** restarted during code deploys. You only need to update them for:

- PostgreSQL version upgrade (yearly)
- Redis version upgrade (yearly)
- Traefik version upgrade (a few times per year)
- Tuning parameter changes (rare)

To update infrastructure:

```bash
cd /srv/ichrisbirch
docker compose --project-name icb-infra -f docker-compose.infra.yml up -d
```

Data persists via named volumes (`icb-prod-postgres-data`, `icb-prod-redis-data`).

## Resource Requirements

| Resource | Minimum | Recommended | Notes |
|----------|---------|-------------|-------|
| RAM | 4 GB | 6 GB | Both colors + build process run simultaneously during deploy |
| Disk | 20 GB | 40 GB | Two sets of images (~1.8 GB), build cache, logs |
| CPU | 2 cores | 4 cores | Parallel image builds benefit from more cores |

Peak memory during deploy: ~3.7 GB (infra ~750 MB + 2x app services ~970 MB each + build overhead).

## Initial Setup (One-Time)

When transitioning from the legacy single-compose deployment to blue/green:

1. Create the state directory on the production server:

   ```bash
   sudo mkdir -p /var/lib/ichrisbirch
   sudo chown chris:chris /var/lib/ichrisbirch
   ```

2. Deploy the new files via git push

3. SSH to production and perform the migration:

   ```bash
   cd /srv/ichrisbirch

   # Start infrastructure (reuses existing named volumes)
   docker compose --project-name icb-infra -f docker-compose.infra.yml up -d

   # Wait for postgres/redis to be healthy
   # Start blue app services
   DEPLOY_COLOR=blue docker compose --project-name icb-blue -f docker-compose.app.yml up -d

   # Verify the site works through the new routing
   curl -sf http://localhost:80/health -H "Host: api.ichrisbirch.com"

   # Stop old containers
   docker compose --project-name icb-prod down

   # Set initial state
   echo "blue" > /var/lib/ichrisbirch/bluegreen-state

   # Clean up old network
   docker network rm icb-prod_default 2>/dev/null || true
   ```

4. Verify with `icb prod deploy-status`

## Monitoring

### Deploy Status

```bash
icb prod deploy-status
```

Shows: active color, infrastructure container status, app container status, routing file state, and any mismatches.

### Slack Notifications

Every deploy sends a Slack notification with:

- Success/failure status
- Commit SHA and message
- Active color
- Duration
- Failed step and error output (on failure)

### Log Locations

| Log | Path | Contents |
|-----|------|----------|
| Deploy log | `/srv/ichrisbirch/logs/deploy.log` | Structured JSON events from each deploy |
| Build logs | `/srv/ichrisbirch/logs/build-*.log` | Docker build output (last 5 kept) |
| Container logs | `docker logs icb-{color}-{service}` | Application stdout/stderr |

## Key Files

| File | Purpose |
|------|---------|
| `docker-compose.infra.yml` | Infrastructure services (Traefik, PostgreSQL, Redis) |
| `docker-compose.app.yml` | Application services parameterized by `${DEPLOY_COLOR}` |
| `docker-compose.yml` | Legacy single-compose fallback |
| `scripts/deploy-homelab.sh` | Blue/green deploy orchestration script |
| `deploy-containers/traefik/dynamic/prod/routing.yml` | Traefik file-provider routing (generated per deploy) |
| `deploy-containers/traefik/dynamic/prod/middlewares.yml` | Traefik middleware definitions |
| `cli/ichrisbirch` | CLI with blue/green-aware commands |
| `cli/health-check.sh` | Health check script (reads active color from state file) |
