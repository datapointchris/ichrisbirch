# Docker Quick Reference

Quick commands and troubleshooting for the ichrisbirch Docker setup.

## Essential Commands

### Development

```bash
# Start development environment
./scripts/dev-start.sh

# Stop development environment
docker-compose --env-file .dev.env -f docker-compose.yml -f docker-compose.dev.yml down

# Rebuild and start
docker-compose --env-file .dev.env -f docker-compose.yml -f docker-compose.dev.yml up --build

# View logs
docker-compose --env-file .dev.env -f docker-compose.yml -f docker-compose.dev.yml logs -f api
```

### Testing

```bash
# Run all tests
./scripts/test-run.sh

# Run specific test file
./scripts/test-run.sh tests/ichrisbirch/api/endpoints/test_habits.py

# Run with coverage
./scripts/test-run.sh --cov=ichrisbirch --cov-report=html
```

### Production

```bash
# Deploy production
docker-compose --env-file .prod.env -f docker-compose.yml -f docker-compose.prod.yml up -d

# Check status
docker-compose --env-file .prod.env -f docker-compose.yml -f docker-compose.prod.yml ps

# View production logs
docker-compose --env-file .prod.env -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

## Debug Commands

### Container Inspection

```bash
# Shell into running container
docker-compose exec api bash

# Run one-off command
docker-compose run --rm api python -c "import ichrisbirch; print('OK')"

# Check environment variables
docker-compose exec api env | grep POSTGRES
```

### Service Health

```bash
# Check if services are running
docker-compose ps

# Test service connectivity
docker-compose exec api ping postgres
docker-compose exec api ping redis

# Check port availability
docker-compose exec api netstat -tlnp
```

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d ichrisbirch_dev

# Check database tables
docker-compose exec postgres psql -U postgres -d ichrisbirch_dev -c "\\dt"

# Connect to Redis
docker-compose exec redis redis-cli
```

## Common Issues

### Port Conflicts

**Error**: `Port 8000 is already in use`

**Solution**:

```bash
# Find process using port
lsof -i :8000

# Stop all containers
docker-compose down

# Start with different ports
# Edit .env file to change FASTAPI_PORT
```

### Database Connection

**Error**: `psycopg2.OperationalError: could not connect to server`

**Solution**:

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check network connectivity
docker-compose exec api ping postgres

# Verify environment variables
docker-compose exec api env | grep POSTGRES
```

### Permission Issues

**Error**: `Permission denied`

**Solution**:

```bash
# Fix file ownership
sudo chown -R $(id -u):$(id -g) .

# Rebuild with correct permissions
docker-compose build --no-cache
```

## Environment Files

### Development (`.dev.env`)

```bash
ENVIRONMENT="development"
POSTGRES_HOST="postgres"
POSTGRES_PORT="5432"
POSTGRES_DB="ichrisbirch_dev"
FASTAPI_HOST="api"
FASTAPI_PORT="8000"
FLASK_HOST="app"
FLASK_PORT="5000"
```

### Testing (`.test.env`)

```bash
ENVIRONMENT="testing"
POSTGRES_HOST="postgres"
POSTGRES_PORT="5432"
POSTGRES_DB="ichrisbirch_test"
FASTAPI_HOST="api"
FASTAPI_PORT="8000"
FLASK_HOST="app"
FLASK_PORT="5000"
```

### Production (`.prod.env`)

```bash
ENVIRONMENT="production"
POSTGRES_HOST="postgres"
POSTGRES_PORT="5432"
POSTGRES_DB="ichrisbirch"
FASTAPI_HOST="api"
FASTAPI_PORT="8000"
FLASK_HOST="app"
FLASK_PORT="5000"
```

## Build Targets

### Development Build

```bash
# Build development image
docker build --target development -t ichrisbirch:dev .

# Features: hot-reload, dev dependencies, debugging
```

### Production Build

```bash
# Build production image
docker build --target production -t ichrisbirch:prod .

# Features: minimal size, security hardening, performance optimized
```

## Service URLs

<http://localhost:8000/docs>

### Development<http://localhost:5000>

- **API Documentation**: <http://localhost:8000/docs>
- **Web Application**: <http://localhost:5000>
- **Database**: localhost:5432
- **Redis**: localhost:6379
<http://localhost:8001/docs>

### Testing<http://localhost:5001>

- **API**: <http://localhost:8001/docs>
- **Web Application**: <http://localhost:5001>
- **Database**: localhost:5434
- **Redis**: localhost:6380
<http://localhost:8000>

### Production<http://localhost:5000>

- **API**: <http://localhost:8000>
- **Web Application**: <http://localhost:5000>
- **Database**: localhost:5432 (if exposed)
- **Redis**: localhost:6379 (if exposed)

## Useful Docker Commands

```bash
# Clean up unused containers, networks, images
docker system prune -a

# View image sizes
docker images

# View container resource usage
docker stats

# Export container filesystem
docker export <container_id> > backup.tar

# Import container filesystem
docker import backup.tar ichrisbirch:backup
```

## Monitoring

### Health Checks

```bash
# Check health status
docker-compose ps

# Manual health check
curl -f http://localhost:8000/health
```

### Resource Usage

```bash
# Container stats
docker stats

# Detailed container info
docker inspect <container_id>

# Process list in container
docker-compose exec api ps aux
```

## Advanced Usage

### Custom Commands

```bash
# Run database migrations
docker-compose run --rm api alembic upgrade head

# Create new migration
docker-compose run --rm api alembic revision --autogenerate -m "description"

# Run Python shell
docker-compose run --rm api python

# Install new package
docker-compose run --rm api poetry add package-name
```

### Volume Management

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect ichrisbirch_postgres_data

# Backup volume
docker run --rm -v ichrisbirch_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/backup.tar.gz /data

# Restore volume
docker run --rm -v ichrisbirch_postgres_data:/data -v $(pwd):/backup alpine sh -c "cd /data && tar xzf /backup/backup.tar.gz --strip 1"
```

This reference should help with day-to-day Docker operations and troubleshooting!
