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

- **Infrastructure**: Proxmox LXC container at `10.0.20.11` with Docker
- **Database**: PostgreSQL restored from AWS backup, working
- **Containers**: All services running (postgres, redis, api, app, chat, scheduler, traefik)
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

The script handles Docker, AWS CLI, cloudflared, repository setup, and database initialization interactively.

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

# Install AWS CLI (for SSM parameter access)
apt install -y awscli

# Clone repository
cd /srv
git clone https://github.com/datapointchris/ichrisbirch.git
cd ichrisbirch

# Install CLI
sudo ln -sf /srv/ichrisbirch/cli/ichrisbirch /usr/local/bin/ichrisbirch

# Set up AWS credentials
mkdir -p ~/.aws
# Copy credentials from local machine or configure
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
|----------|---------|-------|
| ichrisbirch.com | <http://localhost:80> | Flask app (root domain) |
| <www.ichrisbirch.com> | <http://localhost:80> | Flask app (www redirect) |
| api.ichrisbirch.com | <http://localhost:80> | FastAPI backend |
| chat.ichrisbirch.com | <http://localhost:80> | Streamlit chat (enable WebSockets!) |

Traefik routes based on the `Host` header to the appropriate service.

For chat (WebSocket support):

- Click the route → **Additional settings**
- Enable **WebSockets**

## Deployment

### Start Services

```bash
cd /srv/ichrisbirch

# Start production (fetches secrets from SSM, starts all services)
ichrisbirch prod start
```

This will:

- Fetch secrets from AWS SSM (POSTGRES_PASSWORD, REDIS_PASSWORD)
- Create the proxy network if needed
- Start all services via Docker Compose

### Verify Services

```bash
# Check container status
ichrisbirch prod status

# View logs
ichrisbirch prod logs

# Test health endpoints
ichrisbirch prod health

# Check tunnel status
sudo systemctl status cloudflared
```

### Access URLs

Once tunnel is configured:

- **App**: <https://ichrisbirch.com> (also <www.ichrisbirch.com>)
- **API**: <https://api.ichrisbirch.com>
- **Chat**: <https://chat.ichrisbirch.com>

## SSM Parameters

The following SSM parameters are configured for homelab Docker networking:

```bash
# Already configured:
/ichrisbirch/production/postgres/host = "postgres"
/ichrisbirch/production/redis/host = "redis"

# Add for cookie domain:
aws ssm put-parameter --region us-east-2 \
  --name "/ichrisbirch/production/flask/cookie_domain" \
  --value "ichrisbirch.com" --type String --overwrite
```

## CLI Commands

```bash
ichrisbirch prod start    # Fetch SSM secrets and start services
ichrisbirch prod stop     # Stop all services
ichrisbirch prod restart  # Restart without rebuilding
ichrisbirch prod rebuild  # Rebuild images and restart
ichrisbirch prod logs     # View container logs
ichrisbirch prod status   # Check service status
ichrisbirch prod health   # Run health checks
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
ichrisbirch prod status

# View Traefik logs
docker logs ichrisbirch-traefik
```

### WebSocket Issues (Chat)

Ensure WebSockets are enabled in the tunnel route settings for chat.ichrisbirch.com.

### Database Role Does Not Exist

If you see `FATAL: role "ichrisbirch" does not exist`:

```bash
# Create the role (get password from SSM first)
PG_PASS=$(aws ssm get-parameter --region us-east-2 --name "/ichrisbirch/production/postgres/password" --with-decryption --query 'Parameter.Value' --output text)

docker exec ichrisbirch-postgres psql -U postgres -c "CREATE ROLE ichrisbirch WITH LOGIN PASSWORD '$PG_PASS';"
docker exec ichrisbirch-postgres psql -U postgres -c "ALTER ROLE ichrisbirch CREATEDB;"
docker exec ichrisbirch-postgres psql -U postgres -c "ALTER DATABASE ichrisbirch OWNER TO ichrisbirch;"
```

### Database Restore from Backup

If you need to restore from a `.dump` file:

```bash
# Stop app services first
docker stop ichrisbirch-api ichrisbirch-app ichrisbirch-chat ichrisbirch-scheduler

# Terminate existing connections and recreate database
docker exec ichrisbirch-postgres psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'ichrisbirch' AND pid <> pg_backend_pid();"
docker exec ichrisbirch-postgres psql -U postgres -c "DROP DATABASE ichrisbirch;"
docker exec ichrisbirch-postgres psql -U postgres -c "CREATE DATABASE ichrisbirch OWNER ichrisbirch;"

# Restore from dump
cat /path/to/backup.dump | docker exec -i ichrisbirch-postgres pg_restore -U ichrisbirch -d ichrisbirch --no-owner

# Start services
docker start ichrisbirch-api ichrisbirch-app ichrisbirch-chat ichrisbirch-scheduler
```

### SSL/Protocol Errors

If you see `[SSL: WRONG_VERSION_NUMBER]` errors in logs:

The internal services are trying to use HTTPS to communicate, but with Cloudflare Tunnel,
internal communication should be HTTP (Cloudflare handles TLS externally).

Check SSM parameter:

```bash
aws ssm get-parameter --region us-east-2 --name "/ichrisbirch/production/protocol" --query 'Parameter.Value' --output text
```

Should be `http`. If it's `https`, fix it:

```bash
aws ssm put-parameter --region us-east-2 --name "/ichrisbirch/production/protocol" --value "http" --type String --overwrite
```

Then restart services: `ichrisbirch prod restart`

### Volume Naming Issues

Docker Compose prefixes volumes with the project name. If you rebuild with a different project name,
you may get new empty volumes.

The CLI uses `--project-name ichrisbirch-prod`, creating volumes like `ichrisbirch-prod_postgres_data`.

If your data is in differently-named volumes, check:

```bash
docker volume ls | grep postgres
```

You may need to copy data between volumes or update the project name.

## Container Info

- **LXC Host**: ichrisbirch-lxc @ `10.0.20.11`
- **Services**:
  - traefik (port 80, receives tunnel traffic)
  - postgres (5432, Docker internal)
  - redis (6379, Docker internal)
  - api (8000, Docker internal)
  - app (5000, Docker internal)
  - chat (8505, Docker internal)
  - scheduler (no port)
  - cloudflared (tunnel daemon, systemd service)

## Checklist

- [x] LXC container configured for Docker
- [x] Docker and prerequisites installed
- [x] Repository cloned
- [x] CLI installed
- [x] AWS credentials configured
- [x] SSM parameters updated for Docker networking
- [x] Flask cookie settings made configurable
- [x] Traefik configured for Cloudflare Tunnel (HTTP-only)
- [ ] Domain added to Cloudflare
- [ ] Namecheap nameservers updated
- [ ] Cloudflare Tunnel created
- [ ] cloudflared installed and running
- [ ] Tunnel routes configured (pointing to localhost:80)
- [ ] SSM parameter added for cookie domain
- [ ] Full login flow tested
