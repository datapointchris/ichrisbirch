# Deployment Troubleshooting

Production is [blue/green](../blue-green-deployment.md). Infrastructure —
Traefik, PostgreSQL, Redis — runs as `life-infra` and stays up. App services run
as `life-blue` or `life-green`. A deploy starts the color that is not live.

Everything that changes production goes through the deploy pipeline. Reading
logs and container status over SSH is fine. The manual sequences on this page
are for a host where the pipeline itself cannot run.

## Service recovery

### Find out what is live

```bash
lifeops prod deploy-status      # which color, and the sha it is running
lifeops prod status             # container state
lifeops prod logs deploy        # what the last deploy did
```

### Restart or roll back

```bash
lifeops prod restart            # active color plus infrastructure
lifeops prod rollback           # switch traffic back to the previous color
```

`rollback` is the response to a deploy that passed its health checks and then
broke something. The previous color's containers are still up during the grace
period, so the switch is a routing change rather than a rebuild.

### Verify

```bash
lifeops prod health
lifeops prod smoke              # every endpoint
lifeops prod apihealth
```

## A deploy failed

`scripts/deploy-homelab.sh` logs a structured `FAILURE_STEP` for every stage, so
the deploy log names which one stopped it. These are the literal values, in the
order the script sets them, so each one greps the log directly.

```text
  on the host, before any color is touched
    prerequisites ──► decrypt_secrets ──► git_pull
                                              │
  the new color                               ▼
    determine_colors ──► infra_startup ──► pull ──► start_containers
                                                          │
                                                          ▼
    switch_traffic ◄── smoke_tests ◄── migrations ◄── health_check
           │
           ▼
    tear down the old color, after a grace period
```

A failure at any stage before `switch_traffic` leaves the live color serving
traffic. The script tears down the half-started color and exits, and the site
never noticed. The fix is to land a commit, not to intervene on the host.

`migrations` is the one earlier stage that still touches shared state, because
it runs against the same database the live color is using.

### It failed before choosing a color

`prerequisites`, `decrypt_secrets` and `git_pull` run on the host before
blue/green begins, so a failure here means nothing was deployed and nothing
changed.

`decrypt_secrets` exits for three reasons and names which in `FAILURE_OUTPUT`:
`sops` is not installed, `secrets/secrets.prod.enc.env` is missing, or the
decrypt itself failed. The third means the age private key at
`~/.config/sops/age/keys.txt` is absent or wrong, which is what a host rebuild
leaves behind when the key was not copied across.

`git_pull` exits when `git fetch origin main` or `git pull origin main` fails.
A dirty checkout is the usual cause, and it means something edited a tracked
file in `/srv/life/` by hand.

### Images failed to pull

Production does not build. `.github/workflows/release.yml` builds both images
and pushes them to `ghcr.io/datapointchris/`, tagged `sha-<commit>` and
`latest`. A pull failure means that workflow did not finish, or the host cannot
reach GHCR.

Check the workflow run before looking at the host. A red `Release` run is the
whole explanation.

### The build failed in CI

Dev and test read Python code from a bind mount, so they never exercise the
`COPY . /app` that the production target does. A file missing from git, or
excluded by `.dockerignore`, passes both and fails the release build.

Reproduce it locally:

```bash
./ops/lifeops prod build-test
```

### Containers never became healthy

The script waits on Docker health checks. The API's is a `curl` against
`/health`, which needs Postgres and Redis reachable first.

```bash
lifeops prod logs api
lifeops prod logs deploy
```

A container that starts and immediately exits is usually a configuration fault
rather than a code fault. Check that `.env` on the host decrypts and holds
every key `.env.example` lists.

### Migrations failed

Migrations run after the new color is healthy and before routing switches. A
failure here leaves the old color serving traffic against a database the new
code may have partly migrated.

Migrations must be backward-compatible for exactly this reason. The old color
is still running against the same database throughout. A migration that drops a
column the live code reads takes the site down at the moment it succeeds, not
at the moment it fails.

Split a destructive change across two deploys. The first adds and backfills.
The second removes what nothing reads any more.

### Smoke tests failed

`lifeops prod smoke` runs the same checks by hand. They exercise the new color
directly, before it takes traffic. A failure here means the switch never
happened and production is still serving the old color.

## Environment variables

One `.env` per environment, loaded by `python-dotenv`. Production's is
generated from the SOPS-encrypted `secrets/secrets.prod.enc.env`:

```bash
sops secrets/secrets.prod.enc.env
```

`.env.example` lists every key. A service that starts and exits immediately,
with a traceback naming a settings field, is a missing key rather than a bug.

[Configuration](../configuration.md) covers precedence and what each key does.

## Certificates

Production does not manage certificates. Cloudflare Tunnel terminates TLS and
forwards plain HTTP to Traefik on port 80, so there is nothing on the host to
renew and no Let's Encrypt account to expire.

An HTTPS error in production is a Cloudflare problem, a DNS problem, or the
tunnel being down. It is not a certificate on the application host.

Dev and test do have local certificates, generated by mkcert:

```bash
lifeops ssl-manager info dev
lifeops ssl-manager info testing
```

Those live in `deploy-containers/traefik/certs/`. A browser warning on
`app.docker.localhost` means mkcert's CA is not installed in that browser's
trust store.

## Routing

Traefik reads two sources. `routing.yml` is git-tracked and holds routers and
middlewares. `services.yml` is generated by
`scripts/generate-services-yml.sh` and points at the active color.

A path that 404s in production but works in dev is usually a missing Vue path.
Traefik decides between the SPA and the API by prefix, and the prefixes come
from `deploy-containers/traefik/vue-paths.txt`:

```bash
# add the path to vue-paths.txt, then
lifeops routing generate
```

That regenerates all three environments' routing files. Commit them.

## Database

### Connectivity

```bash
lifeops prod status             # is postgres healthy
lifeops prod logs postgres
```

Infrastructure is a separate compose project from the app, and both attach to
the same external network. So a color that cannot reach Postgres is a network
problem rather than a dead database.

### Restore

A restore replaces the whole database, so every write since the dump is gone.
Stop the active color's app services and recreate the database first:

```bash
docker stop life-<color>-api life-<color>-vue life-<color>-scheduler
docker exec life-infra-postgres psql -U postgres -c "DROP DATABASE life WITH (FORCE);"
docker exec life-infra-postgres psql -U postgres -c "CREATE DATABASE life OWNER life;"
```

A gzipped plain SQL dump restores through `psql`. `pg_restore` refuses one with
`input file appears to be a text format dump`:

```bash
gunzip -c <dump-file> | docker exec -i life-infra-postgres \
  psql -U postgres -d life --set ON_ERROR_STOP=1
```

A custom-format dump restores through `pg_restore`:

```bash
docker exec -i life-infra-postgres \
  pg_restore -U life -d life --no-owner --exit-on-error < <dump-file>
```

Then start the services with `docker start`. The bootstrap script takes the same
two formats when it stands a host up.

Backups go to S3, which is the only thing this project uses AWS for. The AWS
CLI is installed by the bootstrap script for that purpose, and
`aws sts get-caller-identity` confirms the host's credentials work.

## Everything is down

Use this only when `lifeops` itself cannot run. It is the sequence
`lifeops prod start` performs.

```bash
# 1. Is it a resource problem
df -h
free -h
docker system df

# 2. Reclaim space if needed
docker system prune -f

# 3. Infrastructure first
cd /srv/life
docker compose --project-name life-infra -f docker-compose.infra.yml up -d

# 4. Wait for Postgres
docker inspect --format='{{.State.Health.Status}}' life-infra-postgres

# 5. The active color's app services
COLOR=$(cat /var/lib/life/bluegreen-state)
DEPLOY_COLOR=$COLOR docker compose \
  --project-name "life-$COLOR" -f docker-compose.app.yml up -d

# 6. Verify
lifeops prod health
lifeops prod smoke
```

Where `/var/lib/life/bluegreen-state` is missing or unreadable, there is
no active color to bring back. `lifeops prod legacy-rebuild` runs the
single-compose path instead, which causes downtime and is a last resort.

## Logs

Two hosts carry logs. The application host runs the containers, and the webhook
host receives the push notification and triggers the deploy.

| What              | Where                               |
| ----------------- | ----------------------------------- |
| Application       | `/srv/life/logs/`, application host |
| Deploy events     | `lifeops prod logs deploy`          |
| Build output      | `lifeops prod logs build`           |
| Webhook receipt   | `/opt/webhooks/logs/`, webhook host |
| One service, live | `lifeops prod logs <service>`       |

A deploy that never started is a webhook-host question. A deploy that started
and failed is an application-host one.

Python logs through structlog, as JSON in production. Requests carry an
`X-Request-ID`, so one request's path through the API is greppable by that id.

## Related

- [Blue/green deployment](../blue-green-deployment.md)
- [Docker troubleshooting](docker-issues.md)
- [Database troubleshooting](database-issues.md)
- [Configuration](../configuration.md)
