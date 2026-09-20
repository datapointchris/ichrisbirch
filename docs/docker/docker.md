# Docker Architecture and Build Process

Two Dockerfiles build the application. `Dockerfile` at the repository root
builds the Python services, and `frontend/Dockerfile` builds the Vue bundle for
production.

## The Python image is one multi-stage build

A build always passes `--target`, because there is no sensible default among
the stages.

| Stage                | From                          | Dependencies installed           |
| -------------------- | ----------------------------- | -------------------------------- |
| `base`               | `uv:python3.14-bookworm-slim` | System packages only             |
| `development`        | `base`                        | Everything, including dev        |
| `testing`            | `base`                        | Production plus the `test` group |
| `production-builder` | `base`                        | Production only                  |
| `production`         | `python:3.14-slim-bookworm`   | Copied from `production-builder` |

`base` installs the system packages every stage needs, including the
PostgreSQL 16 client. Debian 12 ships version 15, so the client comes from the
PostgreSQL project's own apt repository rather than Debian's.

Dependencies are installed with `uv sync --locked`, against `uv.lock`. Each
stage mounts `uv.lock` and `pyproject.toml` rather than copying them, then
copies the source afterwards, so editing application code does not invalidate
the dependency layer.

`production` starts from a plain Python image rather than the `uv` one and
copies `/app` out of `production-builder`. That leaves `uv` itself, the build
caches and the dev dependencies behind. It creates an `app` user and runs as
it.

`development` and `testing` run as root. Both bind-mount the source tree from
the host and run `uv` against it at runtime. Only a root process can write into
a host-owned mount.

## One image runs both Python services

`docker-compose.yml` declares an `x-app-build` anchor and both `api` and
`scheduler` merge it. They differ only in their `command`:

- `api` — `uvicorn ichrisbirch.wsgi_api:api`, four workers in production,
  `--reload` in dev.
- `scheduler` — `python -m ichrisbirch.wsgi_scheduler`.

The two services share a dependency set and a runtime. A second image would
duplicate every layer and change nothing, so they share one.

Production disables uvicorn's access log. Request logging is middleware's job.
Two loggers writing the same requests is two formats to parse.

## The frontend is built for production and not for dev

`frontend/Dockerfile` is two stages. `node:24-alpine` runs `npm ci` and
`npm run build`, then `caddy:2-alpine` takes `/app/dist` and the repository's
`frontend/Caddyfile` and serves the result on port 80. Caddy handles the SPA
fallback, so a deep link renders rather than 404ing.

`VITE_API_URL` is a build argument, not a runtime variable. Vite substitutes it
into the bundle at build time, so changing it means rebuilding the image.
Production passes `/api`, which is the same-origin path Traefik proxies.

Dev and test never build this image. Their `vue` service is a plain
`node:24-alpine` running `npm install && npm run dev`, so Vite's dev server
answers on port 5173 with hot module replacement.

Caddy serves the frontend you deploy and Vite serves the one you develop
against. So a fault in the SPA fallback, or anywhere else in
`frontend/Caddyfile`, cannot show up in dev.

## Dev and test build locally; production pulls

| Environment | Python target | Image                                | Source |
| ----------- | ------------- | ------------------------------------ | ------ |
| Development | `development` | `ichrisbirch:development`            | Built  |
| Testing     | `testing`     | `ichrisbirch:testing`                | Built  |
| CI          | `testing`     | `ichrisbirch:testing`                | Built  |
| Production  | `production`  | `ghcr.io/datapointchris/ichrisbirch` | Pulled |

Production never builds on the server. `.github/workflows/release.yml` builds
both images on a matrix: the root `Dockerfile` at `--target production`, and
`frontend/Dockerfile` with `VITE_API_URL=/api`. It pushes them to GHCR tagged
`sha-<commit>` and `latest`. `docker-compose.app.yml` names those images and has
no `build` section at all. So the deploy pulls a tested artifact rather than
compiling one next to a live database.

Dev and test mount `.:/app` over the image's own copy, so the code that runs is
the code on disk. Both also mount `/app/.venv` as an anonymous volume, which
shadows the bind mount at that one path and keeps the image's virtualenv rather
than the host's. Docker re-seeds an anonymous volume from the image layer on
every new container, so a rebuild picks up dependency changes.

Do not replace that anonymous volume with a named one. A named volume survives
rebuilds, so a stale virtualenv outlives the image that was supposed to fix it,
and the API sits in `health: starting` while `uv` resyncs at runtime.

## Building

`icbops` builds through Compose, which is what selects the target and applies
the overrides:

```bash
./ops/icbops dev rebuild
./ops/icbops testing rebuild
./ops/icbops prod build-test
```

`icbops --help` lists the flags each one takes.

Production is the only target that copies source into the image, so a
`.dockerignore` mistake or an uncommitted file passes dev and test and then
fails in CI. `prod build-test` builds that target locally, which is the build
`release.yml` runs.

## Related

- [Docker Compose Architecture](docker-compose.md)
- [Quick Reference](docker-quick-reference.md)
- [Blue/green deployment](../blue-green-deployment.md)
