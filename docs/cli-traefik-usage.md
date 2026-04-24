# CLI Management Guide

This guide covers the comprehensive CLI interface for managing the iChrisBirch application using modern Traefik deployment.

## 🚀 Quick Reference

```bash
# Start any environment (uses Traefik + HTTPS by default)
icb dev start               # Development environment
icb testing start          # Testing environment
icb prod start             # Production environment

# Check status with URLs
icb dev status

# Run health checks
icb dev health

# SSL certificate management
icb ssl-manager <command> <env>
```

## 📋 Modern CLI Architecture

The CLI has been **completely refactored** to eliminate confusing command duplication. The following changes have been made:

### ✅ **What Changed**

- **Removed all `traefik-*` commands** that duplicated regular environment commands
- **Updated all environment commands** (`dev`, `testing`, `prod`) to use **Traefik + HTTPS by default**
- **Made `ssl-manager` a top-level command** for certificate management
- **Simplified the interface** to hide implementation details from users

### ❌ **Removed Commands (No Longer Needed)**

- `icb traefik start <env>` → Use `ichrisbirch <env> start`
- `icb traefik stop <env>` → Use `ichrisbirch <env> stop`
- `icb traefik status <env>` → Use `ichrisbirch <env> status`
- `icb traefik health <env>` → Use `ichrisbirch <env> health`
- `icb traefik logs <env>` → Use `ichrisbirch <env> logs`

## 🔧 Environment Management Commands

### Development Environment

| Command | Description | Example |
| ------- | ----------- | ------- |
| `dev start` | Start development with HTTPS | `icb dev start` |
| `dev stop` | Stop development environment | `icb dev stop` |
| `dev restart` | Restart development environment | `icb dev restart` |
| `dev rebuild` | Rebuild app image, recreate api/chat/scheduler/vue (keeps infra running) | `icb dev rebuild` |
| `dev rebuild --all` | Full rebuild including infra (traefik, postgres, redis) | `icb dev rebuild --all` |
| `dev rebuild --volumes` | Wipe named volumes and rebuild (stackable with `--all`) | `icb dev rebuild --all --volumes` |
| `dev status` | Show service status, URLs, and credentials | `icb dev status` |
| `dev logs` | View service logs | `icb dev logs [service]` |
| `dev health` | Run comprehensive health checks | `icb dev health` |
| `dev is-ready` | Quick API health check (exit 0/1) | `icb dev is-ready` |
| `dev ensure` | Start containers if not already running | `icb dev ensure` |
| `dev smoke` | Run smoke tests against all endpoints | `icb dev smoke` |
| `dev docker [service]` | Show merged Docker Compose config | `icb dev docker api` |
| `dev db ...` | Database commands (seed, init, reset) | `icb dev db reset` |

**Dev Credentials Display:**

The `dev start`, `dev status`, and `dev rebuild` commands now display development credentials from the `.env` file:

```text
Dev Credentials:
  Regular: user@example.com / password123
  Admin:   admin@example.com / adminpass123
```

### Testing Environment

| Command | Description | Example |
| ------- | ----------- | ------- |
| `test run` | Run tests (reuses containers) | `icb test run [path] [args]` |
| `testing start` | Start testing environment | `icb testing start` |
| `testing stop` | Stop testing environment | `icb testing stop` |
| `testing restart` | Restart testing environment | `icb testing restart` |
| `testing status` | Show service status and HTTPS URLs | `icb testing status` |
| `testing logs` | View service logs | `icb testing logs [service]` |
| `testing health` | Run comprehensive health checks | `icb testing health` |
| `testing rebuild` | Rebuild app image, recreate api/chat/scheduler/vue (keeps infra running) | `icb testing rebuild` |
| `testing rebuild --all` | Full rebuild including infra | `icb testing rebuild --all` |
| `testing rebuild --volumes` | Wipe named volumes and rebuild — step 2 of the code-change escalation ladder (see CLAUDE.md); covers stale `.venv`, deps, node_modules, ENOTEMPTY | `icb testing rebuild --all --volumes` |
| `testing is-ready` | Quick API health check (exit 0/1) | `icb testing is-ready` |
| `testing ensure` | Start containers if not already running | `icb testing ensure` |
| `testing docker [service]` | Show merged Docker Compose config | `icb testing docker api` |
| `testing db ...` | Database commands (seed, init, reset) | `icb testing db reset` |

**Test Run Behavior:**

The `test run` command reuses running containers for fast iteration:

1. **Reuses containers** - Starts test containers only if not already running
2. **Database cleaning** - Handled automatically by pytest's `truncate_tables` fixture (not by the CLI)
3. **No stale connections** - API container's connection pool stays valid across test runs
4. **Fast** - Sub-second database clean vs seconds for drop/recreate

> **Note:** Test and dev environments use separate proxy networks (`icb-test-proxy` and `icb-dev-proxy`) to avoid Traefik routing conflicts when running simultaneously.

### Production Environment

All production commands are **blue/green aware** — they automatically detect the active deployment color and act on the correct containers. See [Blue/Green Deployment](blue-green-deployment.md) for the full guide.

| Command | Description | Example |
| ------- | ----------- | ------- |
| `prod start` | Start infra + active color | `icb prod start` |
| `prod stop` | Stop active color + infra | `icb prod stop` |
| `prod restart` | Restart active color + infra | `icb prod restart` |
| `prod status` | Show infra + active color status | `icb prod status` |
| `prod logs` | View active color logs | `icb prod logs [service]` |
| `prod logs deploy` | View deployment event logs | `icb prod logs deploy` |
| `prod logs build` | View latest Docker build log | `icb prod logs build` |
| `prod health` | Run health checks | `icb prod health` |
| `prod smoke` | Run smoke tests against all endpoints | `icb prod smoke` |
| `prod deploy-status` | Show blue/green state and routing | `icb prod deploy-status` |
| `prod rollback` | Switch traffic to previous color | `icb prod rollback` |
| `prod build-test` | Test production Docker build locally | `icb prod build-test` |
| `prod apihealth` | Check API health endpoint (JSON) | `icb prod apihealth` |
| `prod docker [service]` | Show merged Docker Compose config | `icb prod docker api` |
| `prod db ...` | Database commands (backup, restore, list, init) | `icb prod db backup pre-deploy` |

### SSL Certificate Management

| Command | Description | Example |
| ------- | ----------- | ------- |
| `ssl-manager generate` | Generate SSL certificates with mkcert | `icb ssl-manager generate dev` |
| `ssl-manager validate` | Validate existing certificates | `icb ssl-manager validate dev` |
| `ssl-manager info` | Show certificate information | `icb ssl-manager info dev` |
| `ssl-manager help` | Show SSL manager help | `icb ssl-manager help` |

### Stats Commands

| Command | Description | Example |
| ------- | ----------- | ------- |
| `stats summary` | Dashboard with code, tests, quality, activity | `icb stats summary` |
| `stats code` | Lines of code by language (live from tokei) | `icb stats code` |
| `stats tests` | Test results, coverage, and slowest tests | `icb stats tests` |
| `stats quality` | Linter issues over 24h/7d/30d/all time | `icb stats quality` |
| `stats activity [n]` | Commit activity graph (default: 7 days) | `icb stats activity 14` |
| `stats events [n]` | Recent pre-commit hook events (default: 20) | `icb stats events 50` |
| `stats trends` | Velocity, code churn, test suite trends | `icb stats trends` |
| `stats churn [n\|all]` | File churn analysis (default: 30 days) | `icb stats churn all` |
| `stats snapshot` | Regenerate stats snapshot from events.jsonl | `icb stats snapshot` |

### Routing Commands

| Command            | Description                                   | Example                |
| ------------------ | --------------------------------------------- | ---------------------- |
| `routing generate` | Regenerate Traefik routing from vue-paths.txt | `icb routing generate` |

The canonical path list is at `deploy-containers/traefik/vue-paths.txt`. After generating, the CLI shows a diff of any changes.

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
icb dev start

# Check what's running
icb dev status

# Verify everything is healthy
icb dev health

# View API logs
icb dev logs api

# Stop when done
icb dev stop
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
- **Secrets**: Decrypted via SOPS + age
- **Deployment**: Blue/green with zero-downtime switching

**Services:**

- **API**: `https://api.ichrisbirch.com/`
- **App**: `https://ichrisbirch.com/`
- **Chat**: `https://chat.ichrisbirch.com/`

**Production Commands:**

```bash
icb prod start          # Start infra + active color
icb prod deploy-status  # Check which color is active
icb prod rollback       # Switch to previous color
```

> **Note**: See [Blue/Green Deployment](blue-green-deployment.md) for the deployment strategy and [Homelab Deployment Guide](homelab-deployment.md) for infrastructure setup

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
icb ssl-manager generate dev

# Generate certificates for all environments
icb ssl-manager generate all

# View certificate information
icb ssl-manager info dev
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

### `icb dev start`

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
 ✔ Container icb-dev-vue        Started
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

Use icb dev logs to view live container logs
Use icb dev status to check service status
Use icb dev health to run health checks
```

### `icb dev status`

Shows detailed status of all services with HTTPS URLs and health information.

**Example Output:**

```text
Checking DEV environment status...

Container Status:
[✓] icb-dev-traefik    (Up 2 minutes)
[✓] icb-dev-postgres   (Up 2 minutes (healthy))
[✓] icb-dev-redis      (Up 2 minutes (healthy))
[✓] icb-dev-api        (Up 2 minutes (healthy))
[✓] icb-dev-vue        (Up 2 minutes (healthy))
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

### `icb dev health`

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
[✓] Container: icb-dev-vue (Up 2 minutes (healthy))
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

### `icb dev logs [service]`

View logs for all services or a specific service.

**Usage:**

```bash
icb dev logs          # All services
icb dev logs api      # API service only
icb dev logs traefik  # Traefik logs
```

**Features:**

- **Persistent viewing:** Watch loop automatically reconnects when containers restart
- Real-time log following (Ctrl+C to exit)
- Service-specific filtering
- Colored output for better readability (service names colorized)
- Uses structlog format (timestamp, level, event, context)

### `icb ssl-manager generate <env|all>`

Generates SSL certificates for the specified environment using mkcert when available.

**Usage:**

```bash
icb ssl-manager generate dev    # Development certificates
icb ssl-manager generate all    # All environments
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

### `icb ssl-manager info <env|all>`

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
icb dev restart && icb dev health

# Generate certificates and start environment
icb ssl-manager generate dev && icb dev start

# Check status across all environments
for env in dev testing prod; do
  echo "=== $env ==="
  ichrisbirch $env status
done
```

### Development Workflows

```bash
# Daily development startup
icb dev start

# Quick status check
icb dev status

# View API logs while developing
icb dev logs api

# Clean shutdown at end of day
icb dev stop
```

### Debugging Workflows

```bash
# Troubleshoot service issues
icb dev status          # Check overall status
icb dev logs api        # Check specific service logs
icb dev health          # Run comprehensive health check

# SSL certificate issues
icb ssl-manager validate dev    # Check certificate validity
icb ssl-manager info dev        # Show certificate details
icb ssl-manager generate dev    # Regenerate if needed
```

## 🚨 Troubleshooting

### Common Issues and Solutions

1. **"Command not found" error**

   ```bash
   # Make CLI executable
   chmod +x ./cli/icb

   # Use absolute path
   ./cli/icb dev start
   ```

2. **Port conflicts**

   ```bash
   # Stop conflicting services
   icb dev stop
   docker stop $(docker ps -q --filter "name=ichrisbirch")

   # Restart
   icb dev start
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
   icb ssl-manager generate dev

   # Restart to pick up new certificates
   icb dev restart
   ```

5. **Browser still shows certificate warnings**

   ```bash
   # Verify mkcert is working
   mkcert -install

   # Check certificate details
   icb ssl-manager info dev

   # Clear browser cache and restart browser
   # Chrome: Settings > Privacy > Clear browsing data
   ```

6. **Test containers stuck in restart loop / `npm install` ENOTEMPTY errors**

   A corrupted named volume (usually `icb-test-vue-node-modules` from an interrupted `npm install`) causes the container to crash-loop forever. Use `--volumes` to wipe and rebuild:

   ```bash
   ./cli/icb testing rebuild --all --volumes
   ```

   If the loop has already crashed `dockerd` itself (see `systemctl status docker` showing `inactive (dead)`):

   ```bash
   sudo systemctl reset-failed docker.service docker.socket
   sudo systemctl start docker
   docker rm -f icb-test-vue 2>/dev/null       # kill the loop immediately
   docker volume rm icb-test-vue-node-modules 2>/dev/null
   ./cli/icb testing rebuild --all --volumes
   ```

   See [Docker troubleshooting](troubleshooting/docker-issues.md#container-crash-loop-that-crashes-dockerd) for full recovery procedure.

7. **Containers can reach gateway but not internet (Arch Linux / dual iptables backends)**

   Symptom: one container network has internet, another doesn't. Signature: `docker exec $container ping 1.1.1.1` times out, but pinging the network's gateway works. DNS resolves fine. Root cause: orphan `iptables-legacy` rules referencing dead bridge IDs.

   ```bash
   sudo iptables-legacy -F
   sudo iptables-legacy -t nat -F
   sudo iptables-legacy -X
   sudo systemctl restart docker
   ```

   See [Docker troubleshooting](troubleshooting/docker-issues.md#containers-on-newer-networks-have-no-internet-dual-iptables-backends) for diagnostic commands and permanent prevention.

### Getting Help

```bash
# Show general help
icb help

# Show environment-specific help
icb dev help

# Show SSL manager help
icb ssl-manager help
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

- `icb traefik start dev` vs `icb dev start` (both did the same thing)
- Users had to understand Traefik implementation details
- Inconsistent command patterns
- Implementation details exposed in user interface

### After (Clean & Simple)

- **Single command per operation**: `icb dev start`
- **Implementation details hidden**: Users don't need to know about Traefik
- **Consistent patterns**: All environments work the same way
- **Modern HTTPS by default**: No separate "traefik" commands needed

### User Experience Improvements

- **Faster onboarding**: New developers don't need to understand reverse proxy details
- **Reduced cognitive load**: Fewer commands to remember
- **Better discoverability**: `icb help` shows all available commands clearly
- **Professional CLI patterns**: Follows industry-standard CLI design principles

The simplified CLI provides a clean, professional interface that hides implementation complexity while providing powerful functionality for managing the modern Traefik-based deployment architecture.

````text
