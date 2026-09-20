# Docker

iChrisBirch runs as a set of containers in every environment, orchestrated with
Docker Compose and fronted by Traefik.

`./ops/icbops --help` is the command surface. It covers dev, testing and
production, and it is what these pages point at rather than reproduce — a
`docker compose` line copied into prose goes stale the first time a flag or a
file name changes, and nothing fails when it does.

## Services

Six services, defined in `docker-compose.yml`:

| Service     | What it is                                    |
| ----------- | --------------------------------------------- |
| `traefik`   | Reverse proxy and TLS termination             |
| `api`       | FastAPI backend                               |
| `vue`       | Vue 3 SPA                                     |
| `scheduler` | APScheduler background jobs                   |
| `postgres`  | Application database                          |
| `redis`     | Cache and session storage                     |

## Compose files

`docker-compose.yml` is the base, and dev, test and CI layer over it. Its own
defaults are production ones, down to the `icb-prod-` container names, so a
service read out of the base alone is the production service. Blue/green does
not use it: `docker-compose.infra.yml` and `docker-compose.app.yml` are
standalone.

| File                       | Environment                                        |
| -------------------------- | -------------------------------------------------- |
| `docker-compose.dev.yml`   | Local development                                  |
| `docker-compose.test.yml`  | The test stack, alongside dev on other ports       |
| `docker-compose.ci.yml`    | GitHub Actions                                     |
| `docker-compose.infra.yml` | Production Traefik, Postgres and Redis             |
| `docker-compose.app.yml`   | Production api, vue and scheduler, one color       |

`icbops {dev,testing,prod} docker config [service]` prints the merged result for
an environment, which is the one place the layering is resolved rather than
described.

## Environments

Development is `https://app.docker.localhost/` with the API at
`https://api.docker.localhost/`. Tests run against
`https://api.test.localhost:8443/`.

Production runs on a self-hosted server, not locally. A push to `main` triggers
a webhook that runs `scripts/deploy-homelab.sh`, which deploys the color that
is not live and cuts Traefik over once it is healthy.
`docker-compose.infra.yml` stays up as project `icb-infra`, and
`docker-compose.app.yml` deploys as `icb-blue` or `icb-green`.
[Blue/green deployment](../blue-green-deployment.md) covers the mechanism, and
`icbops prod deploy-status` reports which color is live.

Nothing deploys by hand. `icbops prod start` and `prod restart` bring the live
color back up after a reboot, and they read the color rather than choosing one.

## Configuration

Every environment loads a single `.env` and sets `ENVIRONMENT` to
`development`, `testing` or `production`. `.env.example` lists the keys.
Production secrets are encrypted with SOPS and age at
`secrets/secrets.prod.enc.env`; `sops secrets/secrets.prod.enc.env` edits them
in place. See [Configuration](../configuration.md).

## The images

Two Dockerfiles, because the Python services and the frontend are built
differently.

`Dockerfile` at the root builds `api` and `scheduler`. It is multi-stage —
`base`, `development`, `testing`, `production-builder`, `production` — so a
build always passes `--target`. Dependencies are installed with `uv`. The
`production` stage runs as a non-root user. `development` and `testing` run as
root, because both bind-mount the source tree and run `uv` against it.

`frontend/Dockerfile` builds `vue` for production only. Node builds the bundle
and Caddy serves it on port 80. In dev and test there is no build: the `vue`
service is a plain `node:24-alpine` running `npm install && npm run dev`, so
the Vite dev server is what answers.

Dev and test read Python code from a bind mount rather than from the image, so
a Dockerfile fault can pass both and fail the production build.
`icbops prod build-test` builds the production target locally.

## These pages

- [Docker Architecture and Build Process](docker.md) — the Dockerfile, its
  stages and how an image reaches each environment.
- [Docker Compose Architecture](docker-compose.md) — how the base and the
  per-environment files layer, and the overrides that are not obvious.
- [Quick Reference](docker-quick-reference.md) — the `icbops` verb for each
  common task, and the raw `docker` commands that have no `icbops` equivalent.

## Related

- [Configuration](../configuration.md)
- [Testing](../testing/overview.md)
- [DevOps](../devops/index.md)
- [Troubleshooting](../troubleshooting.md)
