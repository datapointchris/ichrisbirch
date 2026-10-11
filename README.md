# iChrisBirch

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

A personal productivity web application. It tracks tasks, projects, habits,
books, articles, events, countdowns and recipes, and exposes each of them
through a REST API, a browser UI and a command-line client.

## What runs

| Service | Framework | Purpose |
| --- | --- | --- |
| API | FastAPI | REST backend, Authelia ForwardAuth and OIDC auth |
| Vue | Vue 3 + TypeScript | Single-page frontend, every page |
| Scheduler | APScheduler | Daily jobs — autotasks, autofun |

All three share one PostgreSQL database and a Redis cache. Docker Compose runs
them behind Traefik, which terminates TLS and routes by host.

`cli/` is a separate Go module building `icb`, a REST client over the same API.
`ops/icbops` is the bash tool that drives local environments and deploys.

## First run

Requires Docker, [uv](https://docs.astral.sh/uv/), Python 3.14 and Node 24.

```bash
./ops/icbops dev start       # build and start every service, then migrate and add users
./ops/icbops dev health      # confirm the containers are up
```

That serves the app at `https://app.docker.localhost/`, and the API with its
Swagger docs at `https://api.docker.localhost/`.

`./ops/icbops dev db seed --scale 1` fills the database with sample data.

## Tests

```bash
./ops/icbops test run        # Python suite, against its own Postgres and Redis
./ops/icbops test e2e        # Playwright, inside this checkout's test stack
cd frontend && npm test      # TypeScript build check plus unit tests
```

Each pytest session starts and discards its own Postgres and Redis. The e2e
suite runs inside a compose project named after the checkout, which publishes
no ports. So two checkouts run either suite at once without touching each
other or the dev stack.

## Documentation

`mkdocs serve` builds the full documentation at `http://127.0.0.1:8000`. Start
with [Quick Start](docs/quick-start.md), then
[Testing](docs/testing/overview.md) and
[Blue/Green Deployment](docs/blue-green-deployment.md).
