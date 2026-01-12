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

## Prerequisites

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

| Subdomain | Domain | Service |
|-----------|--------|---------|
| app | ichrisbirch.com | <http://localhost:80> |
| api | ichrisbirch.com | <http://localhost:80> |
| chat | ichrisbirch.com | <http://localhost:80> |
| _(empty)_ | ichrisbirch.com | <http://localhost:80> |

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

- **App**: <https://app.ichrisbirch.com>
- **API**: <https://api.ichrisbirch.com>
- **Chat**: <https://chat.ichrisbirch.com>
- **Root**: <https://ichrisbirch.com> (routes to app)

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
