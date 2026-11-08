# Quick Start Guide

Get the Life application running locally with modern Traefik deployment and browser-trusted HTTPS in under 5 minutes.

## 🚀 Prerequisites

### Required Software

- **Docker**: Download from [docker.com](https://docker.com)
- **Docker Compose**: Included with Docker Desktop
- **mkcert**: For browser-trusted SSL certificates

### Install mkcert (Recommended)

mkcert generates **browser-trusted certificates** that eliminate security warnings during development.

```bash
# macOS
brew install mkcert

# Linux
curl -JLO "https://dl.filippo.io/mkcert/latest?for=linux/amd64"
chmod +x mkcert-v*-linux-amd64
sudo cp mkcert-v*-linux-amd64 /usr/local/bin/mkcert

# Install the local Certificate Authority
mkcert -install
```

### Setup Local DNS

Add these entries to your `/etc/hosts` file:

```bash
# Add to /etc/hosts (one-time setup)
echo "127.0.0.1 api.docker.localhost" | sudo tee -a /etc/hosts
echo "127.0.0.1 app.docker.localhost" | sudo tee -a /etc/hosts
echo "127.0.0.1 dashboard.docker.localhost" | sudo tee -a /etc/hosts
```

## ⚡ Quick Start Commands

### 1. Start Development Environment

```bash
# Navigate to project directory
cd life

# Start development environment (includes HTTPS + Traefik automatically)
./ops/lifeops dev start
```

**What this does**:

- Generates SSL certificates (prefers mkcert for browser trust)
- Starts all services with Docker Compose
- Configures Traefik reverse proxy with HTTPS
- Displays access URLs when ready

### 2. Verify Everything Works

```bash
# Check service status and URLs
./ops/lifeops dev status

# Run comprehensive health checks
./ops/lifeops dev health
```

### 3. Access Your Applications

Open these URLs in your browser (**no security warnings with mkcert**):

- **API**: <https://api.docker.localhost/>
- **App**: <https://app.docker.localhost/> (Vue 3 SPA)
- **Dashboard**: <https://dashboard.docker.localhost/> (dev/devpass)

## 🎯 What You Get

### Modern Development Environment

- **✅ Browser-trusted HTTPS**: No certificate warnings with mkcert
- **✅ Automatic service discovery**: Traefik detects services automatically
- **✅ Professional URLs**: Clean subdomain-based routing
- **✅ Built-in monitoring**: Traefik dashboard with real-time metrics
- **✅ Health checks**: Comprehensive service health monitoring

### Simplified CLI Interface

The CLI has been **completely simplified** to eliminate confusing command duplication:

```bash
# Single commands for each operation
./ops/lifeops dev start       # Start development (Traefik + HTTPS automatic)
./ops/lifeops dev status      # Show status + URLs
./ops/lifeops dev health      # Run health checks
./ops/lifeops dev logs        # View service logs
./ops/lifeops dev stop        # Stop development

# SSL certificate management
./ops/lifeops ssl-manager generate dev    # Generate certificates
./ops/lifeops ssl-manager info dev        # Certificate information
```

**No more confusing command duplication** - each operation has exactly one command.

## 🌐 Environment Details

### Development Environment

**Domains**: `*.docker.localhost`
**Port**: 443 (standard HTTPS)
**Certificates**: mkcert browser-trusted

**Services**:

- **FastAPI Backend**: `https://api.docker.localhost/`
- **App Frontend**: `https://app.docker.localhost/` (Vue 3 SPA)
- **Traefik Dashboard**: `https://dashboard.docker.localhost/` (dev/devpass)

> **Note**: All 14 pages are served by Vue 3 at `app.docker.localhost`. Routing is controlled by `deploy-containers/traefik/vue-paths.txt`.

### What's Running

```bash
# Check what's running
./ops/lifeops dev status

# Example output:
# Container Status:
# [✓] life-dev-traefik    (Up 2 minutes)
# [✓] life-dev-postgres   (Up 2 minutes (healthy))
# [✓] life-dev-api        (Up 2 minutes (healthy))
# [✓] life-dev-vue        (Up 2 minutes (healthy))
#
# Development environment URLs:
#   API:       https://api.docker.localhost/
#   APP:       https://app.docker.localhost/
#   DASHBOARD: https://dashboard.docker.localhost/
```

## 🔧 Common Commands

### Daily Development Workflow

```bash
# Start development
./ops/lifeops dev start

# Quick status check
./ops/lifeops dev status

# View API logs while developing
./ops/lifeops dev logs api

# Stop when done
./ops/lifeops dev stop
```

### Troubleshooting

```bash
# Run comprehensive health check
./ops/lifeops dev health

# View specific service logs
./ops/lifeops dev logs traefik    # Traefik proxy logs
./ops/lifeops dev logs api        # API backend logs
./ops/lifeops dev logs vue        # Vue frontend logs

# Restart if needed
./ops/lifeops dev restart
```

### SSL Certificate Management

```bash
# Generate certificates (automatic with mkcert)
./ops/lifeops ssl-manager generate dev

# Check certificate information
./ops/lifeops ssl-manager info dev

# Validate certificates
./ops/lifeops ssl-manager validate dev
```

## 🚨 Quick Troubleshooting

### 1. Browser Shows Certificate Warning

**Problem**: "Not secure" or certificate warning in browser

**Solution**: Install mkcert for browser-trusted certificates

```bash
brew install mkcert
mkcert -install
./ops/lifeops ssl-manager generate dev
./ops/lifeops dev restart
```

### 2. Service Not Accessible

**Problem**: 404 or connection refused

**Solution**: Check service status and health

```bash
./ops/lifeops dev status
./ops/lifeops dev health
./ops/lifeops dev logs
```

### 3. Port Conflicts

**Problem**: "Port already in use" errors

**Solution**: Stop conflicting services

```bash
./ops/lifeops dev stop
docker stop $(docker ps -q --filter "name=life")
./ops/lifeops dev start
```

### 4. DNS Resolution Issues

**Problem**: "Server not found" errors

**Solution**: Check `/etc/hosts` entries

```bash
grep docker.localhost /etc/hosts
# Should show: 127.0.0.1 api.docker.localhost (etc.)
```

## 📚 Next Steps

### Learn More

- **[CLI Management Guide](cli-traefik-usage.md)** - Complete CLI reference
- **[Traefik Deployment Guide](traefik-deployment.md)** - Detailed Traefik configuration
- **[SSL Certificate Troubleshooting](troubleshooting/ssl-certificates.md)** - Certificate issues and solutions
- **[CLI Command Troubleshooting](troubleshooting/cli-commands.md)** - CLI usage and migration guide

### Development Workflows

- **[Developer Setup](developer_setup.md)** - Complete development environment setup
- **[Testing Guide](testing/overview.md)** - Running tests and test environments
- **[Docker Quick Reference](docker/docker-quick-reference.md)** - the `lifeops` verb for each common task

### Other Environments

```bash
# Tests: pytest starts its own Postgres and Redis, and the e2e suite runs
# inside this checkout's test stack, which publishes no ports
./ops/lifeops test run
./ops/lifeops test e2e

# Production environment (runs on homelab, not locally)
# See blue-green-deployment.md
```

> **Note**: Production requires additional setup. See [Homelab Deployment Guide](homelab-deployment.md)

## 🌟 Benefits of Modern Setup

### Compared to Traditional Development

**Traditional (nginx/Apache)**:

- Manual configuration files for each service
- Self-signed certificates with browser warnings
- Manual service discovery and routing updates
- Limited monitoring and debugging tools

**Modern (Traefik + mkcert)**:

- ✅ **Automatic service discovery**: Services appear immediately when started
- ✅ **Browser-trusted HTTPS**: No security warnings during development
- ✅ **Professional URLs**: Clean subdomain-based routing
- ✅ **Built-in monitoring**: Traefik dashboard with real-time metrics
- ✅ **Simplified CLI**: One command per operation, no confusing duplication

### Developer Experience

- **⚡ Faster startup**: Single command starts everything
- **🔒 Secure by default**: HTTPS with trusted certificates
- **🎯 Simple commands**: No need to understand reverse proxy details
- **📊 Better debugging**: Comprehensive health checks and monitoring
- **👥 Team consistency**: Same setup works for all developers

The modern setup provides a **professional development environment** that matches production behavior while being simple enough for daily development use.

---

**🎉 You're ready to develop!** The application should now be running with browser-trusted HTTPS at the URLs above. Check the [CLI Management Guide](cli-traefik-usage.md) for complete command reference.
