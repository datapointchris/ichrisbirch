# Homelab Production Deployment

This document covers deploying ichrisbirch to a Proxmox homelab environment with Docker and Cloudflare Tunnel.

## Architecture

```text
Internet → Cloudflare (SSL/CDN) → Cloudflare Tunnel → Traefik (port 80) → Docker Services
```

- **SSL/TLS**: Handled by Cloudflare (no certificates needed locally)
- **Reverse Proxy**: Traefik handles routing, CORS, security headers, rate limiting
- **No port forwarding**: Tunnel connects outbound, no open ports on router
- **Security**: Home IP hidden behind Cloudflare

## Current Status

- **Infrastructure**: A self-hosted Linux container running Docker
- **Database**: PostgreSQL, in the always-running `icb-infra` project
- **Containers**: All services running (postgres, redis, api, app, scheduler, traefik)
- **External Access**: Via Cloudflare Tunnel

## Quick Start (Bootstrap Script)

For a fresh LXC container, use the bootstrap script:

```bash
# As root on the LXC container
curl -fsSL https://raw.githubusercontent.com/datapointchris/ichrisbirch/master/scripts/bootstrap-homelab.sh | bash
```

Or if you've already cloned the repo:

```bash
sudo ./scripts/bootstrap-homelab.sh
```

The script handles Docker, sops and age, cloudflared, repository setup, secret decryption, and database initialization interactively.

## Manual Setup

### 1. Proxmox LXC Configuration

Ensure LXC has Docker-compatible settings in `/etc/pve/lxc/<id>.conf`:

```yaml
lxc.apparmor.profile: unconfined
lxc.cgroup2.devices.allow: a
lxc.cap.drop:
lxc.mount.auto: proc:rw sys:rw
```

### 2. Container Setup

```bash
# Install prerequisites
apt update && apt install -y curl git

# Install Docker
curl -fsSL https://get.docker.com | sh

# Install age; install sops from https://github.com/getsops/sops/releases
apt install -y age

# Clone repository
cd /srv
git clone https://github.com/datapointchris/ichrisbirch.git
cd ichrisbirch

# Install CLI
sudo ln -sf /srv/ichrisbirch/ops/icbops /usr/local/bin/icbops

# Copy the age private key that decrypts secrets/secrets.prod.enc.env
mkdir -p ~/.config/sops/age
# scp ~/.config/sops/age/keys.txt from your laptop into that directory
```

## Cloudflare Tunnel Setup

### Step 1: Add Domain to Cloudflare

1. Create account at [dash.cloudflare.com](https://dash.cloudflare.com)
2. Click **"Add a site"** → enter `ichrisbirch.com`
3. Select **Free plan**
4. Note the nameservers Cloudflare provides (e.g., `aria.ns.cloudflare.com`)

### Step 2: Update Namecheap DNS

1. Log into [Namecheap](https://namecheap.com)
2. **Domain List** → **Manage** → find **Nameservers**
3. Change to **"Custom DNS"**
4. Enter both Cloudflare nameservers
5. Wait for activation email (10 min - 48 hours, usually ~30 min)

### Step 3: Create Tunnel

1. In Cloudflare: **Zero Trust** → **Networks** → **Tunnels**
2. Click **"Create a tunnel"** → select **"Cloudflared"**
3. Name it `ichrisbirch-homelab`
4. Copy the tunnel token (long string starting with `eyJ...`)

### Step 4: Install cloudflared

On the LXC container:

```bash
# Add Cloudflare repository
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflared.list

# Install
sudo apt update && sudo apt install -y cloudflared

# Install as service with your token
sudo cloudflared service install <YOUR_TUNNEL_TOKEN>

# Verify it's running
sudo systemctl status cloudflared
```

### Step 5: Configure Tunnel Routes

In Cloudflare dashboard, configure **Public Hostnames** for your tunnel.

All routes point to Traefik on port 80, which handles internal routing:

| Hostname | Service | Notes |
| --- | --- | --- |
| ichrisbirch.com | <http://localhost:80> | Flask app (root domain) |
| <www.ichrisbirch.com> | <http://localhost:80> | Flask app (www redirect) |
| api.ichrisbirch.com | <http://localhost:80> | FastAPI backend |

Traefik routes based on the `Host` header to the appropriate service.

## Deployment

Production uses **blue/green deployment** for zero-downtime deploys. See [Blue/Green Deployment](blue-green-deployment.md) for the full guide.

### How It Works

Infrastructure (Traefik, PostgreSQL, Redis) runs in `icb-infra` and is always up. App services deploy as alternating `icb-blue` / `icb-green` projects. Traefik switches routing via a file provider config — no restart needed.

Pushing to `main` triggers the webhook, which runs `scripts/deploy-homelab.sh`. The script builds the new color, verifies health + smoke tests, then switches traffic. If anything fails, the old color keeps serving.

### Start Services

```bash
cd /srv/ichrisbirch

# Start production (blue/green aware — starts infra + active color)
icbops prod start
```

This will:

- Decrypt secrets via SOPS + age
- Start infrastructure services (Traefik, PostgreSQL, Redis) if not running
- Start the active color's app services

### Verify Services

```bash
# Check deployment state (which color is active)
icbops prod deploy-status

# Check container status
icbops prod status

# View logs
icbops prod logs

# Test health endpoints
icbops prod health

# Run smoke tests
icbops prod smoke

# Check tunnel status
sudo systemctl status cloudflared
```

### Rollback

If a problem is discovered after a deploy:

```bash
icbops prod rollback    # Switch traffic back to previous color
```

### Access URLs

Once tunnel is configured:

- **App**: <https://ichrisbirch.com> (also <www.ichrisbirch.com>)
- **API**: <https://api.ichrisbirch.com>

## Configuration

Production settings live in `secrets/secrets.prod.enc.env`, encrypted with SOPS and age.
The deploy pulls `main`, then decrypts that file to `.env`.
The app containers read `.env` through `env_file`.
`icbops prod` commands decrypt it into their own environment instead.

To change a setting, run `sops secrets/secrets.prod.enc.env`, then commit and push.
`POSTGRES_HOST` and `REDIS_HOST` point at the `postgres` and `redis` services in `docker-compose.infra.yml`.

## CLI Commands

```bash
icbops prod start          # Start infra + active color
icbops prod stop           # Stop active color + infra
icbops prod restart        # Restart active color + infra
icbops prod status         # Show container status
icbops prod health         # Run health checks
icbops prod smoke          # Run smoke tests against all endpoints
icbops prod deploy-status  # Show blue/green state and routing
icbops prod rollback       # Switch traffic back to previous color
icbops prod logs           # View container logs
icbops prod logs deploy    # View deployment event logs
icbops prod logs build     # View latest Docker build log
```

## Troubleshooting

### Tunnel Not Connecting

```bash
# Check cloudflared logs
sudo journalctl -u cloudflared -f

# Restart tunnel
sudo systemctl restart cloudflared
```

### Services Not Accessible via Tunnel

```bash
# Verify Traefik is listening
curl -I http://localhost:80

# Check container status
icbops prod status

# View Traefik logs
docker logs icb-prod-traefik
```

### Database Role Does Not Exist

If you see `FATAL: role "icb_app" does not exist`:

```bash
# Create the role (get password from decrypted .env)
PG_PASS=$(grep '^POSTGRES_PASSWORD=' /srv/ichrisbirch/.env | cut -d= -f2- | tr -d '"')

docker exec icb-infra-postgres psql -U postgres -c "CREATE ROLE icb_app WITH LOGIN PASSWORD '$PG_PASS';"
docker exec icb-infra-postgres psql -U postgres -c "ALTER ROLE icb_app CREATEDB;"
docker exec icb-infra-postgres psql -U postgres -c "ALTER DATABASE ichrisbirch OWNER TO icb_app;"
```

### Database Restore from Backup

If you need to restore from a `.dump` file:

```bash
# Stop app services first
docker stop icb-prod-api icb-prod-app icb-prod-scheduler

# Terminate existing connections and recreate database
docker exec icb-infra-postgres psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'ichrisbirch' AND pid <> pg_backend_pid();"
docker exec icb-infra-postgres psql -U postgres -c "DROP DATABASE ichrisbirch;"
docker exec icb-infra-postgres psql -U postgres -c "CREATE DATABASE ichrisbirch OWNER icb_app;"

# Restore from dump
cat /path/to/backup.dump | docker exec -i icb-infra-postgres pg_restore -U icb_app -d ichrisbirch --no-owner

# Start services
docker start icb-prod-api icb-prod-app icb-prod-scheduler
```

### SSL/Protocol Errors

If you see `[SSL: WRONG_VERSION_NUMBER]` errors in logs:

The internal services are trying to use HTTPS to communicate, but with Cloudflare Tunnel,
internal communication should be HTTP (Cloudflare handles TLS externally).

Check `PROTOCOL` in the production settings:

```bash
sops decrypt secrets/secrets.prod.enc.env | grep '^PROTOCOL='
```

It should be `http`. If it is `https`, change it with `sops secrets/secrets.prod.enc.env`, then commit and push so the deploy picks it up.

### Volume Naming Issues

Docker Compose prefixes volumes with the project name. If you rebuild with a different project name,
you may get new empty volumes.

The CLI uses `--project-name icb-prod`, creating volumes like `icb-prod-postgres-data`.

If your data is in differently-named volumes, check:

```bash
docker volume ls | grep postgres
```

You may need to copy data between volumes or update the project name.

## Container Info

- **Application host**: runs every container below; addressed as `$ICB_PROD_HOST`
- **Webhook host**: receives the push notification and runs the deploy; addressed as `$ICB_WEBHOOK_HOST`
- **Infrastructure** (project `icb-infra`, always running):
  - `icb-infra-traefik` (port 80, receives tunnel traffic)
  - `icb-infra-postgres` (5432, Docker internal)
  - `icb-infra-redis` (6379, Docker internal)
- **App Services** (project `icb-blue` or `icb-green`, alternates per deploy):
  - `icb-{color}-api` (8000, Docker internal)
  - `icb-{color}-app` (5000, Docker internal)
  - `icb-{color}-vue` (80, Docker internal)
  - `icb-{color}-scheduler` (no port)
- **System Services**:
  - cloudflared (tunnel daemon, systemd service)
