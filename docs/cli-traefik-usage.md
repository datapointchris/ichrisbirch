# CLI Management Guide

This guide covers the comprehensive CLI interface for managing the iChrisBirch application using modern Traefik deployment.

## 🚀 Quick Reference

```bash
# Start any environment (uses Traefik + HTTPS by default)
ichrisbirch dev start               # Development environment
ichrisbirch testing start          # Testing environment  
ichrisbirch prod start             # Production environment

# Check status with URLs
ichrisbirch dev status

# Run health checks
ichrisbirch dev health

# SSL certificate management
ichrisbirch ssl-manager <command> <env>
```

## 📋 Modern CLI Architecture

The CLI has been **completely refactored** to eliminate confusing command duplication. The following changes have been made:

### ✅ **What Changed**

- **Removed all `traefik-*` commands** that duplicated regular environment commands
- **Updated all environment commands** (`dev`, `testing`, `prod`) to use **Traefik + HTTPS by default**
- **Made `ssl-manager` a top-level command** for certificate management
- **Simplified the interface** to hide implementation details from users

### ❌ **Removed Commands (No Longer Needed)**

- `ichrisbirch traefik start <env>` → Use `ichrisbirch <env> start`
- `ichrisbirch traefik stop <env>` → Use `ichrisbirch <env> stop`  
- `ichrisbirch traefik status <env>` → Use `ichrisbirch <env> status`
- `ichrisbirch traefik health <env>` → Use `ichrisbirch <env> health`
- `ichrisbirch traefik logs <env>` → Use `ichrisbirch <env> logs`

## 🔧 Environment Management Commands

### Development Environment

| Command | Description | Example |
|---------|-------------|---------|
| `dev start` | Start development with HTTPS | `ichrisbirch dev start` |
| `dev stop` | Stop development environment | `ichrisbirch dev stop` |
| `dev restart` | Restart development environment | `ichrisbirch dev restart` |
| `dev rebuild` | Rebuild images, restart, and initialize database | `ichrisbirch dev rebuild` |
| `dev status` | Show service status, URLs, and credentials | `ichrisbirch dev status` |
| `dev logs` | View service logs | `ichrisbirch dev logs [service]` |
| `dev health` | Run comprehensive health checks | `ichrisbirch dev health` |

**Dev Credentials Display:**

The `dev start`, `dev status`, and `dev rebuild` commands now display development credentials from the `.env` file:

```text
Dev Credentials:
  Regular: user@example.com / password123
  Admin:   admin@example.com / adminpass123
```

### Testing Environment

| Command | Description | Example |
|---------|-------------|---------|
| `test run` | Run tests (reuses containers) | `ichrisbirch test run [path] [args]` |
| `test cov` | Run tests with coverage | `ichrisbirch test cov` |
| `testing start` | Start testing environment | `ichrisbirch testing start` |
| `testing stop` | Stop testing environment | `ichrisbirch testing stop` |
| `testing restart` | Restart testing environment | `ichrisbirch testing restart` |
| `testing status` | Show service status and HTTPS URLs | `ichrisbirch testing status` |
| `testing logs` | View service logs | `ichrisbirch testing logs [service]` |
| `testing health` | Run comprehensive health checks | `ichrisbirch testing health` |

**Test Run Behavior:**

The `test run` command uses a clean start strategy for reliability:

1. **Full cleanup** - Stops any existing containers before starting
2. **Fresh start** - New containers with clean database each run
3. **No race conditions** - Handles back-to-back runs reliably (e.g., pre-commit hooks)
4. **Time trade-off** - ~50s startup time accepted for reliability

> **Note:** Test and dev environments use separate proxy networks (`proxy-test` and `proxy-dev`) to avoid Traefik routing conflicts when running simultaneously.

### Production Environment

| Command | Description | Example |
|---------|-------------|---------|
| `prod start` | Start production with HTTPS | `ichrisbirch prod start` |
| `prod stop` | Stop production environment | `ichrisbirch prod stop` |
| `prod restart` | Restart production environment | `ichrisbirch prod restart` |
| `prod status` | Show service status and HTTPS URLs | `ichrisbirch prod status` |
| `prod logs` | View service logs | `ichrisbirch prod logs [service]` |
| `prod health` | Run comprehensive health checks | `ichrisbirch prod health` |

### SSL Certificate Management

| Command | Description | Example |
|---------|-------------|---------|
| `ssl-manager generate` | Generate SSL certificates with mkcert | `ichrisbirch ssl-manager generate dev` |
| `ssl-manager validate` | Validate existing certificates | `ichrisbirch ssl-manager validate dev` |
| `ssl-manager info` | Show certificate information | `ichrisbirch ssl-manager info dev` |
| `ssl-manager help` | Show SSL manager help | `ichrisbirch ssl-manager help` |

## 🌐 Environment Details

### Development Environment (`dev`)

**Characteristics:**

- **Domain**: `*.docker.localhost` (browser-trusted with mkcert)
- **Port**: 443 (standard HTTPS)
- **Dashboard**: `https://dashboard.docker.localhost/` (dev/devpass)

**Services:**

- **API**: `https://api.docker.localhost/`
- **App**: `https://app.docker.localhost/`
- **Chat**: `https://chat.docker.localhost/`

**Example Usage:**

```bash
# Start development environment
ichrisbirch dev start

# Check what's running
ichrisbirch dev status

# Verify everything is healthy
ichrisbirch dev health

# View API logs
ichrisbirch dev logs api

# Stop when done
ichrisbirch dev stop
```

### Testing Environment (`testing`)

**Characteristics:**

- **Domain**: `*.test.localhost` (browser-trusted with mkcert)
- **Port**: 8443 (custom HTTPS port)
- **Dashboard**: `https://dashboard.test.localhost:8443/` (test/testpass)

**Services:**

- **API**: `https://api.test.localhost:8443/`
- **App**: `https://app.test.localhost:8443/`
- **Chat**: `https://chat.test.localhost:8443/`

### Production Environment (`prod`)

**Characteristics:**

- **Domain**: `*.ichrisbirch.com` via Cloudflare Tunnel
- **TLS**: Handled by Cloudflare (Traefik receives HTTP internally)
- **Secrets**: Fetched from AWS SSM Parameter Store

**Services:**

- **API**: `https://api.ichrisbirch.com/`
- **App**: `https://app.ichrisbirch.com/`
- **Chat**: `https://chat.ichrisbirch.com/`

**Production Start:**

```bash
ichrisbirch prod start   # Fetches SSM secrets, then starts services
```

> **Note**: See [Homelab Deployment Guide](homelab-deployment.md) for complete production setup including Cloudflare Tunnel configuration

## 🔒 SSL Certificate Management with mkcert

### Modern Browser-Trusted Certificates

The SSL manager now uses **mkcert** when available to generate **browser-trusted certificates** that work without security warnings.

#### Prerequisites

```bash
# Install mkcert (macOS)
brew install mkcert

# Install mkcert (Linux)
curl -JLO "https://dl.filippo.io/mkcert/latest?for=linux/amd64"
chmod +x mkcert-v*-linux-amd64
sudo cp mkcert-v*-linux-amd64 /usr/local/bin/mkcert

# Install the local CA
mkcert -install
```

#### Generate Certificates

```bash
# Generate certificates for development
ichrisbirch ssl-manager generate dev

# Generate certificates for all environments
ichrisbirch ssl-manager generate all

# View certificate information
ichrisbirch ssl-manager info dev
```

#### What mkcert Provides

- **Browser-trusted certificates**: No security warnings in Chrome, Safari, Firefox
- **Proper Subject Alternative Names**: Wildcard + specific subdomains
- **Local Certificate Authority**: Installed in system trust stores
- **Long validity**: Certificates valid for 2+ years

#### Certificate Domains

**Development certificates include:**

- `docker.localhost`
- `*.docker.localhost`
- `api.docker.localhost`
- `app.docker.localhost`
- `chat.docker.localhost`
- `dashboard.docker.localhost`

## 🚀 Detailed Command Reference

### `ichrisbirch dev start`

Starts the development environment with full Traefik + HTTPS setup.

**What it does:**

- Generates SSL certificates if missing (using mkcert when available)
- Creates Docker networks (`proxy-dev` for development, separate from `proxy-test`)
- Starts all services with Docker Compose
- Waits for services to become healthy
- Displays HTTPS access URLs and dev credentials

**Example Output:**

```text
Starting DEV environment with Docker Compose + Traefik (HTTPS)
[+] Running 8/8
 ✔ Network icb-dev-proxy                Created
 ✔ Container icb-dev-postgres   Healthy
 ✔ Container icb-dev-redis      Started
 ✔ Container icb-dev-api        Started
 ✔ Container icb-dev-app        Started
 ✔ Container icb-dev-chat       Started
 ✔ Container icb-dev-traefik    Started

Development environment started with HTTPS:
  API:       https://api.docker.localhost/
  APP:       https://app.docker.localhost/
  CHAT:      https://chat.docker.localhost/
  DASHBOARD: https://dashboard.docker.localhost/ (user: dev, pass: devpass)

Dev Credentials:
  Regular: user@example.com / password123
  Admin:   admin@example.com / adminpass123

Use ichrisbirch dev logs to view live container logs
Use ichrisbirch dev status to check service status
Use ichrisbirch dev health to run health checks
```

### `ichrisbirch dev status`

Shows detailed status of all services with HTTPS URLs and health information.

**Example Output:**

```text
Checking DEV environment status...

Container Status:
[✓] icb-dev-traefik    (Up 2 minutes)
[✓] icb-dev-postgres   (Up 2 minutes (healthy))
[✓] icb-dev-redis      (Up 2 minutes (healthy))
[✓] icb-dev-api        (Up 2 minutes (healthy))
[✓] icb-dev-app        (Up 2 minutes (healthy))
[✓] icb-dev-chat       (Up 2 minutes)
[✓] icb-dev-scheduler  (Up 2 minutes)

Development environment URLs:
  API:       https://api.docker.localhost/
  APP:       https://app.docker.localhost/
  CHAT:      https://chat.docker.localhost/
  DASHBOARD: https://dashboard.docker.localhost/

Database Info:
  PostgreSQL: localhost:5434 (external access)
  Redis:      localhost:6379 (external access)
```

### `ichrisbirch dev health`

Runs comprehensive health checks for the development environment.

**What it checks:**

- Docker container status and health
- DNS resolution for domains
- HTTPS endpoint accessibility (with proper SSL validation)
- WebSocket support (for chat service)
- Database connectivity
- API health endpoints

**Example Output:**

```text
🏥 Running health check for DEV environment
Health Check for dev Environment
========================================

[INFO] Checking Docker containers for dev environment
[✓] Container: icb-dev-traefik (Up 2 minutes)
[✓] Container: icb-dev-api (Up 2 minutes (healthy))
[✓] Container: icb-dev-app (Up 2 minutes (healthy))
[✓] Container: icb-dev-chat (Up 2 minutes)

[INFO] Checking DNS resolution for api.docker.localhost
[✓] DNS: api.docker.localhost found in /etc/hosts (127.0.0.1)

[INFO] Checking API Health at https://api.docker.localhost/health
[✓] API Health: HTTP 200 (OK)
[INFO] Checking App Frontend at https://app.docker.localhost/
[✓] App Frontend: HTTP 200 (OK)
[INFO] Checking Chat Service at https://chat.docker.localhost/
[✓] Chat Service: HTTP 200 (OK)

[INFO] Checking WebSocket support for Chat Service
[!] Chat Service WebSocket: HTTP 400 (May not support WebSocket)
```

### `ichrisbirch dev logs [service]`

View logs for all services or a specific service.

**Usage:**

```bash
ichrisbirch dev logs          # All services
ichrisbirch dev logs api      # API service only
ichrisbirch dev logs traefik  # Traefik logs
```

**Features:**

- **Persistent viewing:** Watch loop automatically reconnects when containers restart
- Real-time log following (Ctrl+C to exit)
- Service-specific filtering
- Colored output for better readability (service names colorized)
- Uses structlog format (timestamp, level, event, context)

### `ichrisbirch ssl-manager generate <env|all>`

Generates SSL certificates for the specified environment using mkcert when available.

**Usage:**

```bash
ichrisbirch ssl-manager generate dev    # Development certificates
ichrisbirch ssl-manager generate all    # All environments
```

**With mkcert (Recommended):**

- Generates browser-trusted certificates
- Includes proper Subject Alternative Names
- Valid for 2+ years
- No security warnings in browsers

**Fallback (OpenSSL):**

- Self-signed certificates
- May show browser warnings
- Requires manual trust configuration

**Example Output:**

```text
[INFO] Generating SSL certificate for dev environment
[INFO] Using mkcert for trusted local development certificates

Created a new certificate valid for the following names 📜
 - "docker.localhost"
 - "*.docker.localhost"
 - "api.docker.localhost"
 - "app.docker.localhost"
 - "chat.docker.localhost"
 - "dashboard.docker.localhost"

The certificate is at "dev.crt" and the key at "dev.key" ✅
It will expire on 21 January 2028 🗓

[SUCCESS] mkcert certificate generated for dev environment
[INFO] This certificate will be trusted by browsers without warnings
```

### `ichrisbirch ssl-manager info <env|all>`

Displays detailed information about SSL certificates.

**Example Output:**

```text
[INFO] Certificate information for dev environment

Certificate file: /path/to/deploy-containers/traefik/certs/dev.crt
Private key file: /path/to/deploy-containers/traefik/certs/dev.key

Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number: 4e:1c:4c:e9:91:ae:d6:da:1f:91:b1:fc:07:13:9d:f7
        Signature Algorithm: sha256WithRSAEncryption
        Issuer: O=mkcert development CA, CN=mkcert user@hostname
        Validity
            Not Before: Oct 21 23:45:19 2025 GMT
            Not After : Jan 22 00:45:19 2028 GMT
        Subject: O=mkcert development certificate

Valid from: Oct 21 23:45:19 2025 GMT
Valid until: Jan 22 00:45:19 2028 GMT

[SUCCESS] Certificate is valid and not expiring soon
```

## 🔧 Advanced Usage

### Combining Commands

```bash
# Complete environment restart with health check
ichrisbirch dev restart && ichrisbirch dev health

# Generate certificates and start environment
ichrisbirch ssl-manager generate dev && ichrisbirch dev start

# Check status across all environments
for env in dev testing prod; do
  echo "=== $env ==="
  ichrisbirch $env status
done
```

### Development Workflows

```bash
# Daily development startup
ichrisbirch dev start

# Quick status check
ichrisbirch dev status

# View API logs while developing
ichrisbirch dev logs api

# Clean shutdown at end of day
ichrisbirch dev stop
```

### Debugging Workflows

```bash
# Troubleshoot service issues
ichrisbirch dev status          # Check overall status
ichrisbirch dev logs api        # Check specific service logs
ichrisbirch dev health          # Run comprehensive health check

# SSL certificate issues
ichrisbirch ssl-manager validate dev    # Check certificate validity
ichrisbirch ssl-manager info dev        # Show certificate details
ichrisbirch ssl-manager generate dev    # Regenerate if needed
```

## 🚨 Troubleshooting

### Common Issues and Solutions

1. **"Command not found" error**

   ```bash
   # Make CLI executable
   chmod +x ./cli/ichrisbirch

   # Use absolute path
   ./cli/ichrisbirch dev start
   ```

2. **Port conflicts**

   ```bash
   # Stop conflicting services
   ichrisbirch dev stop
   docker stop $(docker ps -q --filter "name=ichrisbirch")

   # Restart
   ichrisbirch dev start
   ```

3. **DNS resolution issues**

   ```bash
   # Check /etc/hosts
   grep docker.localhost /etc/hosts

   # Add missing entries (for development)
   echo "127.0.0.1 api.docker.localhost" | sudo tee -a /etc/hosts
   echo "127.0.0.1 app.docker.localhost" | sudo tee -a /etc/hosts
   echo "127.0.0.1 chat.docker.localhost" | sudo tee -a /etc/hosts
   echo "127.0.0.1 dashboard.docker.localhost" | sudo tee -a /etc/hosts
   ```

4. **Certificate issues in browsers**

   ```bash
   # Install mkcert if not already installed
   brew install mkcert
   mkcert -install

   # Regenerate certificates with mkcert
   ichrisbirch ssl-manager generate dev

   # Restart to pick up new certificates
   ichrisbirch dev restart
   ```

5. **Browser still shows certificate warnings**

   ```bash
   # Verify mkcert is working
   mkcert -install

   # Check certificate details
   ichrisbirch ssl-manager info dev

   # Clear browser cache and restart browser
   # Chrome: Settings > Privacy > Clear browsing data
   ```

### Getting Help

```bash
# Show general help
ichrisbirch help

# Show environment-specific help
ichrisbirch dev help

# Show SSL manager help
ichrisbirch ssl-manager help
```

## 📊 Performance Tips

### Optimizing Startup Time

1. **Keep images up to date**: Regular `docker pull` for base images
2. **Use Docker BuildKit**: Enable for faster builds
3. **Persist volumes**: Avoid unnecessary data recreation

### Monitoring Performance

```bash
# Check container resource usage
docker stats

# Monitor service response times (with trusted certificates)
time curl -I https://api.docker.localhost/health

# View Traefik metrics
curl https://dashboard.docker.localhost/api/overview
```

## 🌟 Benefits of the Simplified CLI

### Before (Confusing Duplication)

- `ichrisbirch traefik start dev` vs `ichrisbirch dev start` (both did the same thing)
- Users had to understand Traefik implementation details
- Inconsistent command patterns
- Implementation details exposed in user interface

### After (Clean & Simple)

- **Single command per operation**: `ichrisbirch dev start`
- **Implementation details hidden**: Users don't need to know about Traefik
- **Consistent patterns**: All environments work the same way
- **Modern HTTPS by default**: No separate "traefik" commands needed

### User Experience Improvements

- **Faster onboarding**: New developers don't need to understand reverse proxy details
- **Reduced cognitive load**: Fewer commands to remember
- **Better discoverability**: `ichrisbirch help` shows all available commands clearly
- **Professional CLI patterns**: Follows industry-standard CLI design principles

The simplified CLI provides a clean, professional interface that hides implementation complexity while providing powerful functionality for managing the modern Traefik-based deployment architecture.

````text
