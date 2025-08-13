# Docker Documentation

This section contains comprehensive documentation for Docker containerization of the iChrisBirch application.

## Overview

The iChrisBirch application runs in a containerized environment using Docker and Docker Compose. This approach provides consistent development, testing, and production environments while simplifying deployment and scaling.

## Architecture

The application consists of multiple services orchestrated through Docker Compose:

- **API Service**: FastAPI backend service handling REST API requests
- **App Service**: Flask frontend service serving web interface
- **Scheduler Service**: Background job processing service
- **PostgreSQL**: Database service for persistent storage
- **Redis**: Caching and session storage service

## Documentation Structure

### Core Documentation

- **[Docker Guide](docker.md)**: Complete Docker setup and usage guide
- **[Docker Compose](docker-compose.md)**: Service orchestration and configuration
- **[Quick Reference](docker-quick-reference.md)**: Essential commands and troubleshooting

### Key Features

- **Multi-stage builds**: Optimized container images for different environments
- **Environment-based configuration**: Separate configs for dev/test/prod
- **Health checks**: Automatic service health monitoring
- **Volume management**: Persistent data storage and development volumes
- **Network isolation**: Secure service communication
- **Dependency management**: Proper service startup ordering

## Quick Start

### Development Environment

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down
```

### Testing Environment

```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run tests
docker-compose -f docker-compose.test.yml exec api pytest

# Cleanup
docker-compose -f docker-compose.test.yml down -v
```

### Production Environment

```bash
# Deploy to production
docker-compose -f docker-compose.prod.yml up -d

# Monitor services
docker-compose -f docker-compose.prod.yml ps

# Update application
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## Environment Configuration

Each environment uses dedicated configuration files:

- **Development**: `.dev.env` - Debug enabled, development database
- **Testing**: `.test.env` - Test database, isolated environment
- **Production**: `.prod.env` - Production database, optimized settings

## Service Management

### Individual Service Operations

```bash
# Start specific service
docker-compose -f docker-compose.dev.yml up api

# View service logs
docker-compose -f docker-compose.dev.yml logs -f app

# Execute commands in service
docker-compose -f docker-compose.dev.yml exec api bash

# Rebuild service
docker-compose -f docker-compose.dev.yml build api
```

### Database Operations

```bash
# Run database migrations
docker-compose -f docker-compose.dev.yml exec api alembic upgrade head

# Access database
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d ichrisbirch

# Backup database
docker-compose -f docker-compose.dev.yml exec postgres pg_dump -U postgres ichrisbirch > backup.sql
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 5000, 8000, 5432, 6379 are available
2. **Permission issues**: Check file permissions in mounted volumes
3. **Service dependencies**: Verify services start in correct order
4. **Environment variables**: Confirm all required env vars are set

### Health Checks

All services include health checks that can be monitored:

```bash
# Check service health
docker-compose -f docker-compose.dev.yml ps

# View detailed health status
docker inspect --format='{{json .State.Health}}' container_name
```

## Security Considerations

- **Non-root user**: All services run as non-root user
- **Network isolation**: Services communicate through Docker networks
- **Secret management**: Sensitive data managed through environment variables
- **Image security**: Regular base image updates and security scanning

## Performance Optimization

- **Multi-stage builds**: Reduced image sizes
- **Layer caching**: Optimized Dockerfile for build performance
- **Resource limits**: Configured memory and CPU limits
- **Volume optimization**: Efficient data persistence strategies

## Related Documentation

- [Configuration](../configuration.md): Application configuration management
- [Testing](../testing/overview.md): Testing strategies and setup
- [DevOps](../devops/index.md): Deployment and infrastructure
- [Troubleshooting](../troubleshooting.md): Common issues and solutions
