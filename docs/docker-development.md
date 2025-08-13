# Docker Development Environment

## Overview

The iChrisBirch project uses Docker Compose for containerized development with separate configurations for development, testing, and production environments.

## Architecture

### Service Configuration

**Development Environment (`docker-compose.dev.yml`)**:

- **Nginx**: Port 80/443 (reverse proxy)
- **Flask App**: Port 8000 (internal), auto-reload enabled
- **FastAPI Backend**: Port 8000 (internal), auto-reload enabled  
- **PostgreSQL**: Port 5432 (internal/external), persistent volumes
- **Redis**: Port 6379 (internal/external), persistent volumes
- **Chat Service**: Port 8505 (internal), auto-reload enabled

**Test Environment (`docker-compose.test.yml`)**:

- **PostgreSQL**: Port 5434 (external) → 5432 (internal), tmpfs for speed
- **Redis**: Port 6380 (external) → 6379 (internal), tmpfs for speed  
- **FastAPI Backend**: Port 8001 (external) → 8000 (internal), isolated test database
- **Nginx**: Disabled for testing

**Production Environment (`docker-compose.yml`)**:

- **All services**: Standard internal ports with production optimizations
- **SSL/TLS**: Ready for certificate mounting
- **Health checks**: Comprehensive monitoring
- **Resource limits**: Production-ready constraints

## CLI Command Reference

### Development Commands

```bash
ichrisbirch dev start     # Start all development services
ichrisbirch dev stop      # Stop and remove containers  
ichrisbirch dev restart   # Restart existing containers
ichrisbirch dev rebuild   # Rebuild images and restart
ichrisbirch dev logs      # View live container logs
ichrisbirch dev status    # Show container status
```

**Technical Details**:

- `restart`: Fast recovery from service crashes (no image rebuild)
- `rebuild`: Full image rebuild after code/dependency changes
- `logs`: Shows Docker infrastructure logs, not application logs

### Test Commands

```bash
ichrisbirch test          # Run pytest in containerized environment
ichrisbirch test logs     # Run tests with timestamped log output
```

**Test Infrastructure**:

- Isolated database on port 5434 with tmpfs for performance
- Redis on port 6380 with tmpfs storage
- Services terminate automatically when tests complete
- Cleanup via `docker-compose down -v` removes test containers/volumes

### Production Commands

```bash
ichrisbirch prod status    # Check production service status
ichrisbirch prod apihealth # HTTP health check for API service
ichrisbirch prod logs      # View production application logs
```

## Docker Compose Configuration

### File Structure

- **`docker-compose.yml`**: Base production configuration
- **`docker-compose.dev.yml`**: Development overrides with debugging
- **`docker-compose.test.yml`**: Test environment with performance optimizations

### Environment Variables

Each environment uses corresponding environment files:

- Development: `.dev.env.secret` (Git Secret encrypted)
- Testing: `.test.env.secret` (Git Secret encrypted)  
- Production: `.prod.env.secret` (Git Secret encrypted)

### Volume Mounts

**Development**:

- Source code mounted for live editing
- Persistent database and Redis volumes
- Nginx configuration from `deploy/dev/nginx/`

**Testing**:

- tmpfs mounts for database and Redis (maximum speed)
- Isolated test data, discarded after tests
- No source code mounts (clean container environment)

**Production**:

- Named volumes for data persistence
- SSL certificate mounting ready
- Optimized configurations from `deploy/prod/`

## Logging Architecture

### Application Logging

- **Python loggers**: Write directly to application log files
- **Log locations**: `$LOG_DIR` environment variable (defaults to `./logs`)
- **Log files**: `ichrisbirch.log`, `app.log`, `api.log`, `scheduler.log`
- **Colored output**: CLI provides colored log viewing with `ichrisbirch logs`

### Container Logging

- **Docker logs**: Infrastructure and startup information only
- **JSON file driver**: Rotation and size limits configured
- **Service tags**: Each service tagged for log identification
- **Access via**: `docker-compose logs` for container-level debugging

## Port Configuration

### External Port Mapping

**Development** (accessible from host):

- Nginx: localhost:80, localhost:443
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- API/App: Through Nginx reverse proxy

**Testing** (isolated ports):

- PostgreSQL: localhost:5434
- Redis: localhost:6380
- FastAPI: localhost:8001

**Production**:

- Nginx: Port 80/443 only (reverse proxy handles internal routing)
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
git secret reveal  # Decrypt environment files

# Start development environment  
ichrisbirch dev start

# View logs
ichrisbirch dev logs
```

### Running Tests

```bash
# Run full test suite
ichrisbirch test

# Run with log output
ichrisbirch test logs

# Check test infrastructure
ichrisbirch dev status
```

### Debugging Services

```bash
# Check service status
docker-compose -f docker-compose.yml -f docker-compose.dev.yml ps

# View specific service logs  
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs api

# Execute commands in running containers
docker exec -it ichrisbirch-api-dev /bin/bash
```

## Production Deployment

### Container Optimization

- **Multi-stage builds**: Development vs production images
- **Security**: Non-root user (`appuser`) for all services
- **Resource limits**: Memory and CPU constraints configured
- **Health monitoring**: Comprehensive health check endpoints

### SSL/TLS Configuration

Ready for certificate mounting:

```yaml
volumes:
  - ./nginx/ssl:/etc/nginx/ssl:ro  # Uncomment for SSL certificates
```

### Scaling Considerations

- **Database**: PostgreSQL optimized for production workloads
- **Redis**: Configured with appropriate memory limits and eviction policies
- **Application services**: Ready for horizontal scaling with load balancer
- **Static files**: Nginx optimized for efficient static file serving

## Troubleshooting

### Common Issues

**Port conflicts**: Development uses standard ports; test uses offset ports to avoid conflicts

**Container permissions**: Services run as `appuser` (UID 1000) for security

**Database connections**: Services include health checks and retry logic for reliable startup

**Volume permissions**: Ensure `$LOG_DIR` is writable by user running Docker Compose

### Debug Commands

```bash
# Check all container status
ichrisbirch dev status

# View recent infrastructure logs
ichrisbirch dev logs

# Clean up unused containers/images  
docker system prune -f

# Reset development environment
ichrisbirch dev stop && ichrisbirch dev rebuild
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
