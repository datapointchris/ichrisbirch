# iChrisBirch Documentation

Welcome to the iChrisBirch application documentation.

## 🚀 Getting Started

- **[Quick Start Guide](quick-start.md)** - Get running in under 5 minutes with modern Traefik deployment and browser-trusted HTTPS

## Architecture

- [Project Layout](project_layout.md) - Overall project structure and organization
- [Configuration](configuration.md) - Environment and settings management
- [Logging Configuration](logging-configuration.md) - Structlog setup, request tracing, and log viewing
- [Dependency Reach](dependency-reach.md) - What each wide-reaching dependency sees and which callers feed it
- [Admin Dashboard](admin.md) - Live log streaming over WebSocket, JWT cookie auth, admin-only access

## Development

- [Developer Setup](developer_setup.md) - Getting started with development
- [Testing](testing/overview.md) - Testing strategy and guidelines
- [Testing Documentation](testing/index.md) - Every testing page: environment, fixtures, test data, writing tests
- [Adding New Apps](add_new_app.md) - How to add new features

## Docker & Deployment

- [Docker](docker/index.md) - the containerized stack, its compose layering and the build
- [Docker Documentation](docker/index.md) - Comprehensive Docker containerization guide
- [Docker Architecture](docker/docker.md) - Multi-stage Docker builds and container strategy
- [Docker Compose](docker/docker-compose.md) - Service orchestration across environments
- [Docker Quick Reference](docker/docker-quick-reference.md) - Common commands and troubleshooting

### Traefik Reverse Proxy (Modern Implementation)

- **[CLI Management Guide](cli-traefik-usage.md)** - Simplified CLI interface with eliminated command duplication
- **[Traefik Deployment Guide](traefik-deployment.md)** - Modern reverse proxy with mkcert browser-trusted certificates

## DevOps

- [CI/CD](cicd.md) - Continuous integration and deployment
- [Homelab Deployment](homelab-deployment.md) - Production deployment with Cloudflare Tunnel
- [Terraform](terraform.md) - Infrastructure as code
- [DevOps](devops/index.md) - Server, database, nginx, supervisor and pg_cron setup notes
- [Blue/Green Deployment](blue-green-deployment.md) - Zero-downtime deploys across alternating app container colors
- [Domain Names](domain_names.md) - Route 53 hosted zones and records for the apex, api and docs domains

## API

- [API Documentation](api/index.md) - Backend API reference
- [Authentication Architecture](authentication-architecture.md) - Modern API key authentication system
- [Authentication Strategies](api/authentication_strategies.md) - Auth implementation details

## Frontend

The frontend is a Vue 3 SPA (TypeScript) served behind `app.docker.localhost` via Traefik path-based routing.

- [Vue Frontend](vue-frontend.md) - Vue 3 architecture, testing, and migration patterns
- [CSS](css.md) - Styling guidelines and SCSS architecture (ITCSS)
- [CSS BEM](css_bem.md) - BEM methodology for CSS
- [HTML5 Semantic](html5_semantic.md) - Semantic HTML structure

## Tools & Utilities

- [Alembic](alembic.md) - Database migrations
- [Scheduler](scheduler.md) - Background job processing
- [Documentation Tools](documentation_tools.md) - Docs generation and maintenance
- [Documentation](documentation.md) - How MkDocs builds these pages and publishes them to gh-pages
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
- [Troubleshooting Guide](troubleshooting/index.md) - Symptoms indexed by component, with root causes and fixes

Docs here
