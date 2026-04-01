# Deployment Troubleshooting

This document covers issues encountered during deployment and production operations of the iChrisBirch project.

## Service Recovery

Production uses [blue/green deployment](../blue-green-deployment.md). Infrastructure (Traefik, PostgreSQL, Redis) runs in `icb-infra`, app services run as `icb-blue` or `icb-green`.

### Quick Service Recovery

#### 1. Check Deployment State

```bash
# What color is active? What's running?
icb prod deploy-status

# Check all containers
docker ps -a | grep icb

# Check deploy logs
icb prod logs deploy
```

#### 2. Restart Services

```bash
# Restart active color + infrastructure
icb prod restart

# If a deploy failed and left the site down, rollback:
icb prod rollback

# Emergency: fall back to legacy single-compose (causes brief downtime)
icb prod legacy-rebuild
```

#### 3. Verify Recovery

```bash
# Test health endpoint
curl -f http://localhost:80/health -H "Host: api.ichrisbirch.com"

# Run full smoke tests
icb prod smoke

# Check container logs
icb prod logs
```

## Build and Deployment Failures

### Docker Build Failures

**Problem:** Production builds fail during deployment.

**Common Causes:**

1. **Dependency conflicts**
2. **Missing environment variables**
3. **Resource limitations**

**Diagnosis:**

```bash
# Build with verbose output
docker-compose -f docker-compose.prod.yml build --no-cache --progress=plain

# Check build context
docker build --dry-run .

# Verify Dockerfile syntax
docker build --target=production .
```

**Resolution:**

```bash
# Clear Docker cache
docker system prune -f
docker builder prune -f

# Rebuild with no cache
docker-compose -f docker-compose.prod.yml build --no-cache

# Check resource usage
docker system df
```

### Environment Variable Issues

**Problem:** Services fail due to missing or incorrect environment variables.

**Diagnosis:**

```bash
# Check environment in container
docker-compose -f docker-compose.prod.yml exec app env | grep -i postgres

# Verify environment file
cat .env.prod
```

**Resolution:**

Ensure all required variables are set:

```bash
# .env.prod
DATABASE_URL=postgresql://user:pass@postgres:5432/ichrisbirch
API_URL=https://yourdomain.com/api
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
```

## SSL/TLS Certificate Issues

### Certificate Expiration

**Problem:** SSL certificates expire causing HTTPS errors.

**Diagnosis:**

```bash
# Check certificate expiration
echo | openssl s_client -connect yourdomain.com:443 | openssl x509 -noout -dates

# Check Let's Encrypt certificates
sudo certbot certificates
```

**Resolution:**

```bash
# Renew certificates
sudo certbot renew

# Test renewal
sudo certbot renew --dry-run

# Restart nginx to load new certificates
docker-compose -f docker-compose.prod.yml restart nginx
```

### Certificate Installation Issues

**Problem:** New certificates not being recognized.

**Resolution:**

```bash
# Update nginx configuration
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# Reload nginx configuration
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload

# Restart nginx service
docker-compose -f docker-compose.prod.yml restart nginx
```

## Database Deployment Issues

### Migration Failures

**Problem:** Database migrations fail during deployment.

**Safe Migration Process:**

```bash
# 1. Backup database first
docker-compose -f docker-compose.prod.yml exec postgres pg_dump \
  -U icb_app ichrisbirch > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Test migrations on backup
docker-compose -f docker-compose.test.yml run test-runner \
  uv run alembic upgrade head

# 3. Apply to production
docker-compose -f docker-compose.prod.yml exec app \
  uv run alembic upgrade head

# 4. Verify migration
docker-compose -f docker-compose.prod.yml exec app \
  uv run python -c "
from ichrisbirch.database import get_sqlalchemy_session
with get_sqlalchemy_session() as session:
    print('Migration successful')
"
```

### Database Connection Issues

**Problem:** Application cannot connect to production database.

**Diagnosis:**

```bash
# Test database connectivity
docker-compose -f docker-compose.prod.yml exec app \
  pg_isready -h postgres -p 5432

# Check database logs
docker-compose -f docker-compose.prod.yml logs postgres
```

## Performance Issues

### High Resource Usage

**Problem:** Production services consuming too many resources.

**Monitoring:**

```bash
# Check container resource usage
docker stats

# Check system resources
htop
df -h
free -h
```

**Resolution:**

```yaml
# docker-compose.prod.yml - Set resource limits
services:
  app:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
```

### Slow Response Times

**Problem:** Application responding slowly to requests.

**Diagnosis:**

```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s http://yourdomain.com/

# Where curl-format.txt contains:
#     time_namelookup:  %{time_namelookup}\n
#        time_connect:  %{time_connect}\n
#     time_appconnect:  %{time_appconnect}\n
#    time_pretransfer:  %{time_pretransfer}\n
#       time_redirect:  %{time_redirect}\n
#  time_starttransfer:  %{time_starttransfer}\n
#                     ----------\n
#          time_total:  %{time_total}\n
```

## Load Balancer and Proxy Issues

### Nginx Configuration Problems

**Problem:** Nginx proxy not routing requests correctly.

**Common Issues:**

1. **Upstream server unavailable**
2. **Wrong proxy configuration**
3. **SSL termination issues**

**Diagnosis:**

```bash
# Test nginx configuration
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# Check nginx logs
docker-compose -f docker-compose.prod.yml logs nginx

# Test upstream connectivity
docker-compose -f docker-compose.prod.yml exec nginx \
  curl -f http://app:8000/health
```

## Backup and Recovery

### Automated Backup Failures

**Problem:** Scheduled backups are failing.

**Check Backup Status:**

```bash
# Check backup cron job
crontab -l

# Check backup logs
tail -f /var/log/backup.log

# Test backup script manually
./scripts/backup.sh
```

**Backup Recovery Process:**

```bash
# List available backups
ls -la /backup/

# Test backup integrity
pg_restore --list backup_20231201_120000.dump

# Restore from backup if needed
docker-compose -f docker-compose.prod.yml down
docker volume rm ichrisbirch_postgres_data
docker-compose -f docker-compose.prod.yml up -d postgres

# Wait for postgres to be ready
sleep 30

# Restore data
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_restore -U icb_app -d ichrisbirch \
  /backup/backup_20231201_120000.dump
```

## Monitoring and Alerting

### Health Check Failures

**Problem:** Health check endpoints returning errors.

**Diagnosis:**

```bash
# Test health endpoints
curl -f http://yourdomain.com/health
curl -f http://yourdomain.com/api/health

# Check internal health
docker-compose -f docker-compose.prod.yml exec app \
  curl -f http://localhost:8000/health
```

**Health Check Implementation:**

```python
# In your application
from fastapi import FastAPI, HTTPException
from ichrisbirch.database import get_sqlalchemy_session

app = FastAPI()

@app.get("/health")
async def health_check():
    """Comprehensive health check."""
    try:
        # Test database connection
        with get_sqlalchemy_session() as session:
            session.execute("SELECT 1")

        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Unhealthy: {str(e)}")
```

### Log Management

**Problem:** Logs growing too large or not being rotated.

**Log Rotation Setup:**

```bash
# Create logrotate configuration
sudo tee /etc/logrotate.d/ichrisbirch << EOF
/var/log/ichrisbirch/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
    postrotate
        docker-compose -f docker-compose.prod.yml restart app
    endscript
}
EOF
```

## Disaster Recovery Procedures

### Complete Service Recovery

**When everything is down:**

```bash
# 1. Check system resources
df -h
free -h
docker system df

# 2. Clean up if needed
docker system prune -f

# 3. Start infrastructure first (postgres, redis, traefik)
cd /srv/ichrisbirch
docker compose --project-name icb-infra -f docker-compose.infra.yml up -d

# 4. Wait for postgres/redis to be healthy
docker inspect --format='{{.State.Health.Status}}' icb-infra-postgres

# 5. Start the active color's app services
COLOR=$(cat /var/lib/ichrisbirch/bluegreen-state)
DEPLOY_COLOR=$COLOR docker compose --project-name icb-$COLOR -f docker-compose.app.yml up -d

# 6. Verify services
icb prod health
icb prod smoke
```

If blue/green state is missing or corrupted, use the legacy fallback:

```bash
icb prod legacy-rebuild
```

### Data Recovery

**If data is corrupted or lost:**

```bash
# 1. Stop application immediately
docker-compose -f docker-compose.prod.yml stop app

# 2. Assess damage
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U icb_app -c "SELECT COUNT(*) FROM users;"

# 3. Restore from most recent backup
# (Use backup recovery procedure)

# 4. Verify data integrity
# (Run data validation queries)

# 5. Resume service
docker-compose -f docker-compose.prod.yml start app
```

## Prevention and Monitoring

### Deployment Checklist

Before each deployment:

- [ ] Run tests in staging environment
- [ ] Backup production database
- [ ] Verify environment variables
- [ ] Test migration scripts
- [ ] Check disk space and resources
- [ ] Verify SSL certificate validity
- [ ] Update deployment documentation

### Monitoring Setup

**Essential monitoring:**

```bash
# System monitoring
htop
iotop
nethogs

# Docker monitoring
docker stats
docker system df

# Application monitoring
curl -f http://yourdomain.com/health
```

**Automated monitoring script:**

```bash
#!/bin/bash
# scripts/monitor.sh

# Check service health
check_service() {
    if curl -f -s http://localhost/$1/health > /dev/null; then
        echo "✓ $1 service healthy"
    else
        echo "✗ $1 service unhealthy"
        # Send alert here
    fi
}

check_service "api"
check_service ""  # Main app

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "⚠️  Disk usage high: ${DISK_USAGE}%"
fi

# Check memory
MEMORY_USAGE=$(free | awk 'NR==2{print $3/$2 * 100.0}')
if (( $(echo "$MEMORY_USAGE > 80" | bc -l) )); then
    echo "⚠️  Memory usage high: ${MEMORY_USAGE}%"
fi
```

Run monitoring periodically:

```bash
# Add to crontab
*/5 * * * * /path/to/scripts/monitor.sh >> /var/log/monitoring.log 2>&1
```
