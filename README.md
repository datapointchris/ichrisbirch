# iChrisBirch

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

A personal productivity web application. It tracks tasks, projects, habits,
books, articles, events, countdowns and recipes, and exposes each of them
through a REST API, a browser UI and a command-line client.

## What runs

| Service | Framework | Purpose |
| --- | --- | --- |
| API | FastAPI | REST backend, JWT and Authelia OIDC auth |
| Vue | Vue 3 + TypeScript | Single-page frontend, every page |
| Scheduler | APScheduler | Daily jobs — task priorities, autotasks |

All three share one PostgreSQL database and a Redis cache. Docker Compose runs
them behind Traefik, which terminates TLS and routes by host.

`cli/` is a separate Go module building `icb`, a REST client over the same API.
`ops/icbops` is the bash tool that drives local environments and deploys.

## First run

Requires Docker, [uv](https://docs.astral.sh/uv/), Python 3.14 and Node 24.

```bash
./ops/icbops dev db init     # create schemas, run migrations, add users
./ops/icbops dev start       # build and start every service
./ops/icbops dev health      # confirm the containers are up
```

That serves the app at `https://app.docker.localhost/`, and the API with its
Swagger docs at `https://api.docker.localhost/`.

`./ops/icbops dev db seed --scale 1` fills the database with sample data.

## Tests

```bash
./ops/icbops test run        # Python suite; starts test containers if needed
cd frontend && npm test      # TypeScript build check plus unit tests
cd frontend && npm run test:e2e   # Playwright, through Traefik
```

The Python tests run against their own containers and database, isolated from
the dev stack and reachable at `https://api.test.localhost:8443/`.

## Documentation

`mkdocs serve` builds the full documentation at `http://127.0.0.1:8000`. Start
with [Quick Start](docs/quick-start.md), then
[Testing](docs/testing/overview.md) and
[Blue/Green Deployment](docs/blue-green-deployment.md).
