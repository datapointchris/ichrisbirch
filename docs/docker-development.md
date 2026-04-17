# Docker Development Environment

## Overview

The iChrisBirch project uses Docker Compose for containerized development with separate configurations for development, testing, and production environments.

## Architecture

### Service Configuration

**Development Environment (`docker-compose.dev.yml`)**:

- **Traefik**: Port 443 (reverse proxy with HTTPS, `*.docker.localhost`)
- **FastAPI Backend**: Port 8000 (internal), auto-reload enabled
- **Vue Frontend**: Port 5173 (Vite dev server)
- **PostgreSQL**: Port 5432 (internal/external), persistent volumes
- **Redis**: Port 6379 (internal/external), persistent volumes
- **Chat Service**: Port 8505 (internal), auto-reload enabled
- **Scheduler**: APScheduler background jobs

**Test Environment (`docker-compose.test.yml`)**:

- **Traefik**: Port 8443 (HTTPS), `*.test.localhost`
- **PostgreSQL**: Port 5434 (external) → 5432 (internal), tmpfs for speed
- **Redis**: Port 6380 (external) → 6379 (internal), no persistence
- **FastAPI Backend**: Port 8001 (external) → 8000 (internal), isolated test database

**Production Environment** (`docker-compose.infra.yml` + `docker-compose.app.yml`):

- **Blue/green deployment**: Infrastructure always running, app services alternate between blue/green
- **Zero downtime**: New containers verified via health checks + smoke tests before traffic switches
- **Traefik file provider**: Routing controlled by `routing.yml`, hot-reloaded on change
- **Health checks**: Comprehensive monitoring on all services
- See [Blue/Green Deployment](blue-green-deployment.md) for the full guide

## CLI Command Reference

### Development Commands

```bash
icb dev start     # Start all development services
icb dev stop      # Stop and remove containers
icb dev restart   # Restart existing containers
icb dev rebuild   # Rebuild images and restart
icb dev logs      # View live container logs
icb dev status    # Show container status
```

**Technical Details**:

- `restart`: Fast recovery from service crashes (no image rebuild)
- `rebuild`: Full image rebuild after code/dependency changes
- `logs`: Shows Docker infrastructure logs, not application logs

### Test Commands

```bash
icb test          # Run pytest in containerized environment
icb test logs     # Run tests with timestamped log output
```

**Test Infrastructure**:

- Isolated database on port 5434 with tmpfs for performance
- Redis on port 6380 with tmpfs storage
- Services terminate automatically when tests complete
- Cleanup via `docker-compose down -v` removes test containers/volumes

### Production Commands

```bash
icb prod start          # Start infra + active color
icb prod stop           # Stop active color + infra
icb prod restart        # Restart without rebuilding
icb prod status         # Check production service status
icb prod health         # Run health checks
icb prod apihealth      # HTTP health check for API service
icb prod smoke          # Run smoke tests against all endpoints
icb prod deploy-status  # Show blue/green state and routing
icb prod rollback       # Switch traffic back to previous color
icb prod logs           # View production application logs
```

## Docker Compose Configuration

### File Structure

- **`docker-compose.yml`**: Base configuration (shared service definitions)
- **`docker-compose.dev.yml`**: Development overrides (thin — only deltas from base, uses `!override` for list fields)
- **`docker-compose.test.yml`**: Test overrides (thin — tmpfs, alternate ports, uses `!override`)
- **`docker-compose.ci.yml`**: CI overrides (no local mounts, internal network)
- **`docker-compose.infra.yml`**: Production infrastructure (Traefik, PostgreSQL, Redis) — always running
- **`docker-compose.app.yml`**: Production app services parameterized by `${DEPLOY_COLOR}` for blue/green

Use `ich {dev,testing,prod} docker config [service]` to see fully merged output.

See [Blue/Green Deployment](blue-green-deployment.md) for details on the production compose split.

### Environment Variables

Each environment uses `.env` files:

- Development/Testing: `.env` (from `.env.example`)
- Production: Decrypted from `secrets/secrets.prod.enc.env` (SOPS + age encrypted)

### Volume Mounts

**Development**:

- Source code bind-mounted for live editing (`.:/app`)
- Persistent database and Redis volumes
- AWS credentials mounted read-only

**Testing**:

- tmpfs for database (no persistence, maximum speed)
- Source code bind-mounted, anonymous `.venv` volume seeded fresh from the image (matches dev)
- Isolated test data, discarded on `testing stop`

**Production (blue/green)**:

- Code baked into Docker image (no bind mounts)
- Named volumes for data persistence
- See [Blue/Green Deployment](blue-green-deployment.md)

## Logging Architecture

### Application Logging

- **Python services (API, Scheduler)**: structlog with stdout-only output. Key=value format for dev, JSON for production/Loki.
- **Vue frontend**: consola with structured reporters matching structlog's format. Includes request tracing via X-Request-ID headers.
- **Colored output**: CLI provides colored log viewing with `icb dev logs`

### Container Logging

- **Docker logs**: Infrastructure and startup information only
- **JSON file driver**: Rotation and size limits configured
- **Service tags**: Each service tagged for log identification
- **Access via**: `docker-compose logs` for container-level debugging

## Port Configuration

### External Port Mapping

**Development** (accessible from host):

- Traefik: localhost:443 (HTTPS reverse proxy)
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- API/Vue/Chat: Through Traefik reverse proxy at `*.docker.localhost`

**Testing** (isolated ports):

- PostgreSQL: localhost:5434
- Redis: localhost:6380
- FastAPI: localhost:8001

**Production**:

- Traefik: Port 80 only (Cloudflare handles TLS externally)
- All other services: Internal container network only

### Service Communication

- **Internal network**: All services communicate via container names
- **Health checks**: Services wait for dependencies before starting
- **Service discovery**: Automatic via Docker Compose networking

## Development Workflow

### Starting Development

```bash
# Clone and setup
git clone <repository>
cd ichrisbirch
cp .env.example .env  # Configure environment variables

# Start development environment
icb dev start

# View logs
icb dev logs
```

### Running Tests

```bash
# Run full test suite
ichrisbirch test

# Run with log output
icb test logs

# Check test infrastructure
icb dev status
```

### Debugging Services

```bash
# Check service status
docker-compose -f docker-compose.yml -f docker-compose.dev.yml ps

# View specific service logs
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs api

# Execute commands in running containers
docker exec -it icb-dev-api /bin/bash
```

## Production Deployment

### Container Optimization

- **Multi-stage builds**: Development vs production images
- **Security**: Non-root user (`appuser`) for all services
- **Resource limits**: Memory and CPU constraints configured
- **Health monitoring**: Comprehensive health check endpoints

### Scaling Considerations

- **Database**: PostgreSQL optimized for production workloads
- **Redis**: Configured with appropriate memory limits and eviction policies

## Troubleshooting

### Common Issues

**Port conflicts**: Development uses standard ports; test uses offset ports to avoid conflicts

**Container permissions**: Services run as `appuser` (UID 1000) for security

**Database connections**: Services include health checks and retry logic for reliable startup

**Volume permissions**: Ensure `$LOG_DIR` is writable by user running Docker Compose

### Debug Commands

```bash
# Check all container status
icb dev status

# View recent infrastructure logs
icb dev logs

# Clean up unused containers/images
docker system prune -f

# Reset development environment
icb dev stop && icb dev rebuild
```

### Performance Optimization

**Development**: Persistent volumes with live code reloading

**Testing**: tmpfs mounts eliminate I/O bottlenecks for test database/Redis

**Production**: Optimized PostgreSQL and Redis configurations for production workloads

## Migration from Legacy Setup

### Key Changes

- **Containerized services**: All services now run in Docker containers
- **Environment isolation**: Separate configurations for dev/test/prod
- **Modern authentication**: API key-based internal service authentication
- **Health monitoring**: Comprehensive health checks and monitoring
- **Simplified deployment**: Single command deployment with Docker Compose

### Compatibility

- **Existing workflows**: CLI commands maintain same interface
- **Log viewing**: Same colored log output with enhanced container support
- **Development experience**: Hot reloading and debugging capabilities preserved
- **Production deployment**: Enhanced reliability and monitoring capabilities
