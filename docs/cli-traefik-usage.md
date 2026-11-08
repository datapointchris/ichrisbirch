# CLI Management Guide

This guide covers the comprehensive CLI interface for managing the Life application using modern Traefik deployment.

## 🚀 Quick Reference

```bash
# Start any environment (uses Traefik + HTTPS by default)
lifeops dev start               # Development environment
lifeops testing start          # Testing environment
lifeops prod start             # Production environment

# Check status with URLs
lifeops dev status

# Run health checks
lifeops dev health

# SSL certificate management
lifeops ssl-manager <command> <env>
```

## 📋 Modern CLI Architecture

The CLI has been **completely refactored** to eliminate confusing command duplication. The following changes have been made:

### ✅ **What Changed**

- **Removed all `traefik-*` commands** that duplicated regular environment commands
- **Updated all environment commands** (`dev`, `testing`, `prod`) to use **Traefik + HTTPS by default**
- **Made `ssl-manager` a top-level command** for certificate management
- **Simplified the interface** to hide implementation details from users

### ❌ **Removed Commands (No Longer Needed)**

- `life traefik start <env>` → Use `life <env> start`
- `life traefik stop <env>` → Use `life <env> stop`
- `life traefik status <env>` → Use `life <env> status`
- `life traefik health <env>` → Use `life <env> health`
- `life traefik logs <env>` → Use `life <env> logs`

## 🔧 Environment Management Commands

### Development Environment

| Command | Description | Example |
| --- | --- | --- |
| `dev start` | Start development with HTTPS | `lifeops dev start` |
| `dev stop` | Stop development environment | `lifeops dev stop` |
| `dev restart` | Restart development environment | `lifeops dev restart` |
| `dev rebuild` | Rebuild app image, recreate api/scheduler/vue (keeps infra running) | `lifeops dev rebuild` |
| `dev rebuild --all` | Full rebuild including infra (traefik, postgres, redis) | `lifeops dev rebuild --all` |
| `dev rebuild --volumes` | Wipe named volumes and rebuild (stackable with `--all`) | `lifeops dev rebuild --all --volumes` |
| `dev status` | Show service status, URLs, and credentials | `lifeops dev status` |
| `dev logs` | View service logs | `lifeops dev logs [service]` |
| `dev health` | Run comprehensive health checks | `lifeops dev health` |
| `dev is-ready` | Quick API health check (exit 0/1) | `lifeops dev is-ready` |
| `dev ensure` | Start containers if not already running | `lifeops dev ensure` |
| `dev smoke` | Run smoke tests against all endpoints | `lifeops dev smoke` |
| `dev docker [service]` | Show merged Docker Compose config | `lifeops dev docker api` |
| `dev db ...` | Database commands (seed, init, reset) | `lifeops dev db reset` |

`dev start`, `dev restart` and every `dev rebuild` variant end by initializing the database. Initialization is idempotent, so an existing database only receives pending migrations. `dev rebuild` also seeds it.

**Dev Credentials Display:**

The `dev start`, `dev status`, and `dev rebuild` commands now display development credentials from the `.env` file:

```text
Dev Credentials:
  Regular: user@example.com / password123
  Admin:   admin@example.com / adminpass123
```

### Testing Environment

| Command | Description | Example |
| --- | --- | --- |
| `test run` | Run pytest against its own throwaway Postgres and Redis | `lifeops test run [path] [args]` |
| `test e2e` | Run Playwright inside this checkout's test stack, starting it if needed | `lifeops test e2e [spec] [args]` |
| `testing start` | Remove stacks whose checkout is gone, start this one | `lifeops testing start` |
| `testing stop` | Stop this checkout's stack and remove its volumes | `lifeops testing stop` |
| `testing restart` | Restart testing environment | `lifeops testing restart` |
| `testing status` | Show the project name and each service's state | `lifeops testing status` |
| `testing logs` | View service logs | `lifeops testing logs [service]` |
| `testing health` | Run comprehensive health checks | `lifeops testing health` |
| `testing rebuild` | Rebuild app image, recreate api/scheduler/vue (keeps infra running) | `lifeops testing rebuild` |
| `testing rebuild --all` | Full rebuild including infra | `lifeops testing rebuild --all` |
| `testing rebuild --volumes` | Wipe named volumes and rebuild — step 2 of the code-change escalation ladder (see CLAUDE.md); covers stale `.venv`, deps, node_modules, ENOTEMPTY | `lifeops testing rebuild --all --volumes` |
| `testing is-ready` | Quick check that every service is healthy (exit 0/1) | `lifeops testing is-ready` |
| `testing ensure` | Start containers if not already running | `lifeops testing ensure` |
| `testing docker [service]` | Show merged Docker Compose config | `lifeops testing docker api` |
| `testing db ...` | Database commands (seed, init, reset) | `lifeops testing db reset` |

`testing start`, `testing restart` and every `testing rebuild` variant end by initializing the database. The test Postgres keeps its data on tmpfs, so any recreate of it starts empty, and a rebuild hands back a database the suite can run against with no second step.

**Each checkout has its own stack.** The `testing` verbs act on the compose project `life-test-<checkout directory>`, which publishes no ports. Two worktrees run their stacks side by side, and `testing stop` in one leaves the other running. Every verb but `testing stop` refuses a stack another checkout with the same directory name started.

**`test run` never touches the stack.** Each pytest session starts its own Postgres and Redis through testcontainers, migrates them to head and discards them at the end. [Test Environment](testing/environment.md) covers both suites.

### Production Environment

All production commands are **blue/green aware** — they automatically detect the active deployment color and act on the correct containers. See [Blue/Green Deployment](blue-green-deployment.md) for the full guide.

| Command | Description | Example |
| --- | --- | --- |
| `prod start` | Start infra + active color | `lifeops prod start` |
| `prod stop` | Stop active color + infra | `lifeops prod stop` |
| `prod restart` | Restart active color + infra | `lifeops prod restart` |
| `prod status` | Show infra + active color status | `lifeops prod status` |
| `prod logs` | View active color logs | `lifeops prod logs [service]` |
| `prod logs deploy` | View deployment event logs | `lifeops prod logs deploy` |
| `prod logs build` | View latest Docker build log | `lifeops prod logs build` |
| `prod health` | Run health checks | `lifeops prod health` |
| `prod smoke` | Run smoke tests against all endpoints | `lifeops prod smoke` |
| `prod deploy-status` | Show blue/green state and routing | `lifeops prod deploy-status` |
| `prod rollback` | Switch traffic to previous color | `lifeops prod rollback` |
| `prod build-test` | Test production Docker build locally | `lifeops prod build-test` |
| `prod apihealth` | Check API health endpoint (JSON) | `lifeops prod apihealth` |
| `prod docker [service]` | Show merged Docker Compose config | `lifeops prod docker api` |
| `prod db ...` | Database commands (backup, restore, list, init) | `lifeops prod db backup pre-deploy` |

### SSL Certificate Management

| Command | Description | Example |
| --- | --- | --- |
| `ssl-manager generate` | Generate SSL certificates with mkcert | `lifeops ssl-manager generate dev` |
| `ssl-manager validate` | Validate existing certificates | `lifeops ssl-manager validate dev` |
| `ssl-manager info` | Show certificate information | `lifeops ssl-manager info dev` |
| `ssl-manager help` | Show SSL manager help | `lifeops ssl-manager help` |

### Stats Commands

| Command | Description | Example |
| --- | --- | --- |
| `stats summary` | Dashboard with code, tests, quality, activity | `lifeops stats summary` |
| `stats code` | Lines of code by language (live from tokei) | `lifeops stats code` |
| `stats tests` | Test results, coverage, and slowest tests | `lifeops stats tests` |
| `stats quality` | Linter issues over 24h/7d/30d/all time | `lifeops stats quality` |
| `stats activity [n]` | Commit activity graph (default: 7 days) | `lifeops stats activity 14` |
| `stats events [n]` | Recent pre-commit hook events (default: 20) | `lifeops stats events 50` |
| `stats trends` | Velocity, code churn, test suite trends | `lifeops stats trends` |
| `stats churn [n\|all]` | File churn analysis (default: 30 days) | `lifeops stats churn all` |
| `stats snapshot` | Regenerate stats snapshot from events.jsonl | `lifeops stats snapshot` |

### Routing Commands

| Command | Description | Example |
| --- | --- | --- |
| `routing generate` | Regenerate Traefik routing from vue-paths.txt | `lifeops routing generate` |

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

**Example Usage:**

```bash
# Start development environment
lifeops dev start

# Check what's running
lifeops dev status

# Verify everything is healthy
lifeops dev health

# View API logs
lifeops dev logs api

# Stop when done
lifeops dev stop
```

### Testing Environment (`testing`)

**Characteristics:**

- **Project**: `life-test-<checkout directory>`, one per checkout
- **Ports**: none published to the host
- **Dashboard**: none

**Services**, reachable only from inside the stack, where the e2e suite runs:

- **API**: `https://api.test.localhost:8443/`
- **App**: `https://app.test.localhost:8443/`

### Production Environment (`prod`)

**Characteristics:**

- **Domain**: `*.ichrisbirch.com` via Cloudflare Tunnel
- **TLS**: Handled by Cloudflare (Traefik receives HTTP internally)
- **Secrets**: Decrypted via SOPS + age
- **Deployment**: Blue/green with zero-downtime switching

**Services:**

- **API**: `https://life.ichrisbirch.com/api/v1/`, and the same path on `https://ichrisbirch.com`
- **App**: `https://life.ichrisbirch.com/`, and `https://ichrisbirch.com/`

**Production Commands:**

```bash
lifeops prod start          # Start infra + active color
lifeops prod deploy-status  # Check which color is active
lifeops prod rollback       # Switch to previous color
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
lifeops ssl-manager generate dev

# Generate certificates for all environments
lifeops ssl-manager generate all

# View certificate information
lifeops ssl-manager info dev
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
- `dashboard.docker.localhost`

## 🚀 Detailed Command Reference

### `lifeops dev start`

Starts the development environment with full Traefik + HTTPS setup.

**What it does:**

- Generates SSL certificates if missing (using mkcert when available)
- Creates the `life-dev-proxy` network, which no test stack shares
- Starts all services with Docker Compose
- Waits for services to become healthy
- Displays HTTPS access URLs and dev credentials

**Example Output:**

```text
Starting DEV environment with Docker Compose + Traefik (HTTPS)
[+] Running 8/8
 ✔ Network life-dev-proxy                Created
 ✔ Container life-dev-postgres   Healthy
 ✔ Container life-dev-redis      Started
 ✔ Container life-dev-api        Started
 ✔ Container life-dev-vue        Started
 ✔ Container life-dev-traefik    Started

Development environment started with HTTPS:
  API:       https://api.docker.localhost/
  APP:       https://app.docker.localhost/
  DASHBOARD: https://dashboard.docker.localhost/ (user: dev, pass: devpass)

Dev Credentials:
  Regular: user@example.com / password123
  Admin:   admin@example.com / adminpass123

Use lifeops dev logs to view live container logs
Use lifeops dev status to check service status
Use lifeops dev health to run health checks
```

### `lifeops dev status`

Shows detailed status of all services with HTTPS URLs and health information.

**Example Output:**

```text
Checking DEV environment status...

Container Status:
[✓] life-dev-traefik    (Up 2 minutes)
[✓] life-dev-postgres   (Up 2 minutes (healthy))
[✓] life-dev-redis      (Up 2 minutes (healthy))
[✓] life-dev-api        (Up 2 minutes (healthy))
[✓] life-dev-vue        (Up 2 minutes (healthy))
[✓] life-dev-scheduler  (Up 2 minutes)

Development environment URLs:
  API:       https://api.docker.localhost/
  APP:       https://app.docker.localhost/
  DASHBOARD: https://dashboard.docker.localhost/
```

### `lifeops dev health`

Runs comprehensive health checks for the development environment.

**What it checks:**

- Docker container status and health
- DNS resolution for domains
- HTTPS endpoint accessibility (with proper SSL validation)
- Database connectivity
- API health endpoints

**Example Output:**

```text
🏥 Running health check for DEV environment
Health Check for dev Environment
========================================

[INFO] Checking Docker containers for dev environment
[✓] Container: life-dev-traefik (Up 2 minutes)
[✓] Container: life-dev-api (Up 2 minutes (healthy))
[✓] Container: life-dev-vue (Up 2 minutes (healthy))

[INFO] Checking DNS resolution for api.docker.localhost
[✓] DNS: api.docker.localhost found in /etc/hosts (127.0.0.1)

[INFO] Checking API Health at https://api.docker.localhost/health
[✓] API Health: HTTP 200 (OK)
[INFO] Checking App Frontend at https://app.docker.localhost/
[✓] App Frontend: HTTP 200 (OK)
```

### `lifeops {dev|testing|prod} logs [service] [flags]`

View logs for all services or a specific service. Backed by `ops/log_viewer.py`,
a structured renderer that JSON-decodes structlog lines from life
containers and falls through to passthrough rendering for third-party services
(traefik, postgres, redis).

**Usage:**

```bash
lifeops dev logs                                 # All services
lifeops dev logs api                             # API only
lifeops dev logs --level WARNING                 # Filter by level
lifeops dev logs --request-id abc12345           # Follow one request across services
lifeops dev logs --module CountdownsStore        # Filter by structlog logger / Vue module
lifeops dev logs --event task_created            # Filter by event name substring
lifeops dev logs --grep 'pattern'                # Arbitrary regex filter
lifeops dev logs --no-callsite                   # Hide file:line for denser output
lifeops dev logs --json                          # Raw JSON passthrough (for piping to jq)
lifeops dev logs --no-follow                     # Print recent and exit
```

The same flags work for `lifeops testing logs ...` and `lifeops prod logs ...`.

**Features:**

- Watch loop automatically reconnects when containers restart
- Service-name colorization for non-JSON lines
- Structured rendering with optional callsite (`file.py:42`)
- Cross-service request tracing via `--request-id`
- Dev / test default to `LOG_FORMAT=json` so the viewer always sees structured input

### `lifeops ssl-manager generate <env|all>`

Generates SSL certificates for the specified environment using mkcert when available.

**Usage:**

```bash
lifeops ssl-manager generate dev    # Development certificates
lifeops ssl-manager generate all    # All environments
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
 - "dashboard.docker.localhost"

The certificate is at "dev.crt" and the key at "dev.key" ✅
It will expire on 21 January 2028 🗓

[SUCCESS] mkcert certificate generated for dev environment
[INFO] This certificate will be trusted by browsers without warnings
```

### `lifeops ssl-manager info <env|all>`

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
lifeops dev restart && lifeops dev health

# Generate certificates and start environment
lifeops ssl-manager generate dev && lifeops dev start

# Check status across all environments
for env in dev testing prod; do
  echo "=== $env ==="
  lifeops $env status
done
```

### Development Workflows

```bash
# Daily development startup
lifeops dev start

# Quick status check
lifeops dev status

# View API logs while developing
lifeops dev logs api

# Clean shutdown at end of day
lifeops dev stop
```

### Debugging Workflows

```bash
# Troubleshoot service issues
lifeops dev status          # Check overall status
lifeops dev logs api        # Check specific service logs
lifeops dev health          # Run comprehensive health check

# SSL certificate issues
lifeops ssl-manager validate dev    # Check certificate validity
lifeops ssl-manager info dev        # Show certificate details
lifeops ssl-manager generate dev    # Regenerate if needed
```

## 🚨 Troubleshooting

### Common Issues and Solutions

1. **"Command not found" error**

   ```bash
   # Make CLI executable
   chmod +x ./ops/lifeops

   # Use absolute path
   ./ops/lifeops dev start
   ```

2. **Port conflicts**

   ```bash
   # Stop conflicting services
   lifeops dev stop
   docker stop $(docker ps -q --filter "name=life-dev-")

   # Restart
   lifeops dev start
   ```

3. **DNS resolution issues**

   ```bash
   # Check /etc/hosts
   grep docker.localhost /etc/hosts

   # Add missing entries (for development)
   echo "127.0.0.1 api.docker.localhost" | sudo tee -a /etc/hosts
   echo "127.0.0.1 app.docker.localhost" | sudo tee -a /etc/hosts
   echo "127.0.0.1 dashboard.docker.localhost" | sudo tee -a /etc/hosts
   ```

4. **Certificate issues in browsers**

   ```bash
   # Install mkcert if not already installed
   brew install mkcert
   mkcert -install

   # Regenerate certificates with mkcert
   lifeops ssl-manager generate dev

   # Restart to pick up new certificates
   lifeops dev restart
   ```

5. **Browser still shows certificate warnings**

   ```bash
   # Verify mkcert is working
   mkcert -install

   # Check certificate details
   lifeops ssl-manager info dev

   # Clear browser cache and restart browser
   # Chrome: Settings > Privacy > Clear browsing data
   ```

6. **Test containers stuck in restart loop / `npm install` ENOTEMPTY errors**

   A corrupted named volume (usually `life-test-<checkout>-vue-node-modules` from an interrupted `npm install`) causes the container to crash-loop forever. Use `--volumes` to wipe and rebuild:

   ```bash
   ./ops/lifeops testing rebuild --all --volumes
   ```

   If the loop has already crashed `dockerd` itself (see `systemctl status docker` showing `inactive (dead)`):

   ```bash
   sudo systemctl reset-failed docker.service docker.socket
   sudo systemctl start docker
   project=life-test-<checkout>
   docker rm -f "$project-vue" 2>/dev/null     # kill the loop immediately
   docker volume rm "$project-vue-node-modules" 2>/dev/null
   ./ops/lifeops testing rebuild --all --volumes
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
lifeops help

# Show environment-specific help
lifeops dev help

# Show SSL manager help
lifeops ssl-manager help
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

- `life traefik start dev` vs `lifeops dev start` (both did the same thing)
- Users had to understand Traefik implementation details
- Inconsistent command patterns
- Implementation details exposed in user interface

### After (Clean & Simple)

- **Single command per operation**: `lifeops dev start`
- **Implementation details hidden**: Users don't need to know about Traefik
- **Consistent patterns**: All environments work the same way
- **Modern HTTPS by default**: No separate "traefik" commands needed

### User Experience Improvements

- **Faster onboarding**: New developers don't need to understand reverse proxy details
- **Reduced cognitive load**: Fewer commands to remember
- **Better discoverability**: `lifeops help` shows all available commands clearly
- **Professional CLI patterns**: Follows industry-standard CLI design principles

The simplified CLI provides a clean, professional interface that hides implementation complexity while providing powerful functionality for managing the modern Traefik-based deployment architecture.

````text
