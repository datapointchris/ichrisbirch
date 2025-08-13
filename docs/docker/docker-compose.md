# Docker Compose Architecture

This document details how Docker Compose orchestrates the ichrisbirch application services across different environments.

## Overview

The ichrisbirch application uses a **layered Docker Compose approach** where:

1. **Base configuration** (`docker-compose.yml`) defines core services
2. **Environment-specific overrides** customize behavior for dev/test/prod
3. **Environment files** (`.dev.env`, `.test.env`, `.prod.env`) inject configuration

## File Structure

```text
docker-compose.yml           # Base service definitions
docker-compose.dev.yml       # Development overrides
docker-compose.test.yml      # Testing overrides  
docker-compose.prod.yml      # Production overrides
.dev.env                     # Development environment variables
.test.env                    # Testing environment variables
.prod.env                    # Production environment variables
```

## Base Configuration (`docker-compose.yml`)

### Core Services

```yaml
services:
  postgres:    # PostgreSQL database
  redis:       # Redis cache/session store
  api:         # FastAPI backend service
  app:         # Flask frontend service
  scheduler:   # Background job scheduler
```

### Service Communication

All services communicate via Docker's internal network using **service names**:

- `postgres:5432` - Database server
- `redis:6379` - Redis server  
- `api:8000` - FastAPI backend
- `app:5000` - Flask frontend

### Port Mapping Strategy

**Internal Ports** (container-to-container): Always the same
**External Ports** (host access): Environment-specific

| Service | Internal Port | Dev External | Test External | Prod External |
|---------|---------------|--------------|---------------|---------------|
| API     | 8000          | 8000         | 8001          | 8000          |
| App     | 5000          | 5000         | 5001          | 5000          |
| PostgreSQL | 5432       | 5432         | 5434          | 5432          |
| Redis   | 6379          | 6379         | 6380          | 6379          |

## Environment Overrides

### Development Override (`docker-compose.dev.yml`)

**Purpose**: Enable development features

**Key Features**:

- Volume mounts for live editing

**Example Override**:
services:
  api:
    build:
      target: development
    command: uvicorn ichrisbirch.wsgi_api:api --host 0.0.0.0 --port 8000 --reload --log-level debug
    volumes:
      - .:/app

```yaml


### Testing Override (`docker-compose.test.yml`)





- Test runner service


**Example Override**:

```yaml

  postgres:
    tmpfs:
      - /var/lib/postgresql/data  # In-memory database

    environment:
      POSTGRES_DB: ichrisbirch_test


  test-runner:

    build: .

    depends_on:

        condition: service_healthy


### Production Override (`docker-compose.prod.yml`)


**Purpose**: Production-optimized configuration

**Key Features**:
- Production build target
- Gunicorn with multiple workers
- Health checks
- No volume mounts (security)
- Nginx reverse proxy

**Example Override**:

```yaml
services:
  api:
    build:
      target: production
    command: gunicorn ichrisbirch.wsgi_api:api --bind 0.0.0.0:8000 --workers 4
    volumes: []  # No development mounts
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
```

## Environment Variables

### Environment File Usage

Each environment uses its own `.env` file:

```bash
# Development
docker-compose --env-file .dev.env -f docker-compose.yml -f docker-compose.dev.yml up

# Testing  
docker-compose --env-file .test.env -f docker-compose.yml -f docker-compose.test.yml up

# Production
docker-compose --env-file .prod.env -f docker-compose.yml -f docker-compose.prod.yml up
```

### Variable Precedence

1. **Command line** (`-e` flag)
2. **Shell environment** (`export VAR=value`)
3. **Environment file** (`--env-file .env`)
4. **Compose file** (`environment:` section)
5. **Dockerfile** (`ENV` instruction)

### Key Configuration Variables

```bash
# Environment identification
ENVIRONMENT=development|testing|production

# Database configuration  
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=ichrisbirch_dev
POSTGRES_USERNAME=postgres
POSTGRES_PASSWORD=postgres

# Redis configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=""

# Application configuration
FASTAPI_HOST=api
FASTAPI_PORT=8000
FLASK_HOST=app
FLASK_PORT=5000
```

## Service Dependencies

### Dependency Chain

```text
postgres (database)
├── redis (cache)
├── api (backend)
│   └── app (frontend)
│   └── scheduler (background jobs)
└── test-runner (testing only)
```

### Service Health Dependencies

Services wait for dependencies to be healthy:

```yaml
services:
  api:
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
```

## Build Integration

### How Compose Uses Dockerfile

Docker Compose extends the Dockerfile with:

1. **Build Context**: Sets working directory
2. **Target Selection**: Chooses build stage
3. **Build Arguments**: Passes variables to build
4. **Image Naming**: Tags built images

### Build Configuration

```yaml
services:

      context: .              # Build context (project root)
      dockerfile: Dockerfile  # Dockerfile location
      target: development     # Build stage
      args:
        POETRY_VERSION: 1.8.3
```

## Network Architecture

### Internal Network

Docker Compose creates an isolated network where:

- Services communicate via service names
- No external access unless ports are mapped
- Internal DNS resolution (e.g., `ping postgres`)

### External Access

Only mapped ports are accessible from host:

```yaml
services:
  api:
    ports:
      - "8000:8000"  # Host:Container
```

## Volume Management

### Development Volumes

```yaml
volumes:
  - .:/app                    # Live code editing
  - /app/.venv               # Exclude virtual environment
  - postgres_data:/var/lib/postgresql/data  # Database persistence
```

### Production Volumes

```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data  # Database only
  # No source code mounts for security
```

### Volume Types

- **Bind mounts**: Host directory → Container (`./src:/app/src`)
- **Named volumes**: Docker-managed storage (`postgres_data:/var/lib/postgresql/data`)
- **Tmpfs mounts**: In-memory storage (`tmpfs: /tmp`)

## Operational Commands

### Development Workflow

```bash
# Start development environment
./scripts/dev-start.sh

# View logs
docker-compose --env-file .dev.env -f docker-compose.yml -f docker-compose.dev.yml logs -f

# Execute commands in running container
docker-compose --env-file .dev.env -f docker-compose.yml -f docker-compose.dev.yml exec api bash

# Restart specific service
docker-compose --env-file .dev.env -f docker-compose.yml -f docker-compose.dev.yml restart api
```

### Testing Workflow

```bash
# Run tests
./scripts/test-run.sh

# Run specific test
./scripts/test-run.sh tests/ichrisbirch/api/endpoints/test_habits.py


# Debug test failures
docker-compose --env-file .test.env -f docker-compose.yml -f docker-compose.test.yml run --rm test-runner bash
```

### Production Workflow

```bash

# Deploy production
docker-compose --env-file .prod.env -f docker-compose.yml -f docker-compose.prod.yml up -d

# Check health

# Scale services

docker-compose --env-file .prod.env -f docker-compose.yml -f docker-compose.prod.yml up -d --scale api=3
```

## Security Considerations

### Development Security

- Local network isolation
- Non-root container execution
- Volume mounts limited to necessary files

- No source code mounts

- Secrets via environment variables
- Network isolation with reverse proxy
- Health checks for monitoring

### Environment Isolation

Each environment has:

- Separate databases
- Isolated networks
- Environment-specific secrets
- Different external ports

## Monitoring and Debugging

### Health Checks

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  start_period: 5s
  retries: 3
```

### Logging

```bash
# View all logs
docker-compose logs

# Follow specific service
docker-compose logs -f api

# Filter by timestamp
docker-compose logs --since 2024-01-01T00:00:00 api
```

### Resource Monitoring

```bash
# Resource usage
docker-compose exec api top

# System stats
docker stats

# Service status
docker-compose ps
```

## Best Practices

### 1. Environment Consistency

- Use same service names across environments
- Maintain consistent internal ports
- Only vary external configuration

### 2. Service Independence

- Each service has its own container
- Services communicate via well-defined APIs
- No shared file systems between services

### 3. Configuration Management

- Environment variables for all configuration
- Separate `.env` files per environment
- No hardcoded values in compose files

### 4. Development Experience

- Hot-reload for rapid iteration
- Volume mounts for live editing
- Comprehensive logging and debugging

### 5. Production Readiness

- Health checks for all services
- Proper restart policies
- Resource limits and reservations
- Security hardening

## Summary

This Docker Compose architecture provides:

- **Environment Parity**: Same services, different configurations
- **Service Isolation**: Each component in its own container
- **Configuration Flexibility**: Environment-specific overrides
- **Development Efficiency**: Hot-reload and live editing
- **Production Readiness**: Health checks and scaling
- **Security**: Proper isolation and access controls

The layered approach allows for maximum flexibility while maintaining consistency across all environments.
