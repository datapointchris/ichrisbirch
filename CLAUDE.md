# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

iChrisBirch is a personal productivity web application with a **multi-service architecture**: FastAPI backend (API), Flask frontend (App, being replaced by Vue), Vue 3 SPA frontend, Streamlit chat interface, and APScheduler service. All services share a PostgreSQL database and Redis cache, orchestrated via Docker Compose with Traefik reverse proxy.

**Package Management**: uv for Python (`uv.lock`), npm for Vue (`package-lock.json`)

## Essential Commands

```bash
# Development
./cli/ichrisbirch dev start|stop|restart|rebuild|status|health|logs

# Testing (reuses containers, resets database each run)
./cli/ichrisbirch test run              # All tests
./cli/ichrisbirch test run <path> -v    # Specific test
./cli/ichrisbirch test cov              # With coverage
./cli/ichrisbirch testing start|stop|health|logs  # Container management

# Vue frontend
cd frontend && npm test                 # Build check + unit tests
cd frontend && npm run test:e2e         # Playwright E2E through Traefik

# Database
alembic revision --autogenerate -m "description"
alembic upgrade head

# Code quality
uv run ruff check . && uv run ruff format .
uv run mypy ichrisbirch/
pre-commit run --all-files
```

**Dev URLs**: `https://app.docker.localhost/`, `https://api.docker.localhost/`, `https://chat.docker.localhost/`

**Test URL**: `https://api.test.localhost:8443/`

## Production Environment

**Production runs on the homelab, NOT locally.**

- **Production server**: `ssh chris@10.0.20.11` — path: `/srv/ichrisbirch/`
- **Webhook server**: `ssh chris@10.0.20.15` — webhook code lives at `~/homelab`
- **Deployment**: Push to main triggers webhook rebuild. Logs at `/srv/ichrisbirch/logs/`

```bash
# View production logs (read-only SSH)
ssh chris@10.0.20.11 "docker logs icb-prod-api --tail=50 2>&1"
ssh chris@10.0.20.11 "docker logs icb-prod-vue --tail=50 2>&1"
ssh chris@10.0.20.11 "docker logs icb-prod-app --tail=50 2>&1"
ssh chris@10.0.20.11 "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

# Webhook server logs (if containers never started)
ssh chris@10.0.20.15 "ls -lt /opt/webhooks/logs/ichrisbirch-*.log | head -5"
```

## Architecture

### Services

| Service | Framework | Purpose |
|---------|-----------|---------|
| API | FastAPI | RESTful backend, JWT + Authelia auth |
| App | Flask | Legacy SSR frontend (being replaced by Vue) |
| Vue | Vue 3 + TypeScript | Modern SPA frontend, nearly all pages migrated |
| Chat | Streamlit | AI chat interface with OpenAI |
| Scheduler | APScheduler | Daily jobs (task priorities, autotasks, S3 backup) |

Core directories: `ichrisbirch/` (Python backend), `frontend/` (Vue 3 SPA), `tests/` (Python test suite). See the filesystem for the full structure.

### Vue Frontend

The Vue app incrementally replaces Flask pages via Traefik path-based routing (Vue at priority 100, Flask catchall at priority 50). Nearly all pages are migrated — only Admin remains on Flask.

**Key patterns:**

- Pinia stores with `ApiError`, structured logging via `createLogger()`, `error: ref<ApiError | null>`
- `useTheme` composable: OKLCH color themes, named themes (from `~/tools/theme/`), accent hue slider, 14 fonts
- E2E tests run through `app.docker.localhost` (not `vue.docker.localhost`) to catch CORS issues
- Self-hosted fonts in `frontend/public/fonts/` (woff2)

**Critical:** Every new Vue path or static asset path (`/fonts`, `/profile`, etc.) must be added to Traefik PathPrefix rules in **ALL THREE** compose files (dev, test, prod). Flask catches anything not routed to Vue.

**CORS gotcha:** Wildcard `Access-Control-Allow-Headers: *` does NOT work with `credentials: true` — list headers explicitly in Traefik middleware config (including `X-Request-ID`).

### Authentication

**Authelia (Production):** ForwardAuth on `ichrisbirch.com` routes, injects `Remote-User`/`Remote-Email` headers. `api.ichrisbirch.com` bypasses ForwardAuth (for JWT/API key clients like MCP tools). Config in `~/homelab`.

**Vue (Production):** Same-origin proxy — Vue calls `/api/...`, Traefik `api-proxy` router (priority 200) strips `/api` prefix and forwards to FastAPI. No CORS needed.

**Vue (Dev):** Cross-origin — Vue calls `https://api.docker.localhost` directly. Traefik `dev-authelia-sim` middleware injects `Remote-User: user@icb.com`.

**FastAPI:** JWT tokens (access 15min, refresh 7d) + Authelia `Remote-User` header (highest priority) + Personal API Keys. Protected routes use `Depends(auth.get_current_user)`.

**Flask:** Flask-Login sessions + CSRF via Flask-WTF.

### Configuration & Secrets

- All environments use `.env` files (loaded via `python-dotenv`), set `ENVIRONMENT=development|testing|production`
- **Secrets**: SOPS + age — encrypted at `secrets/secrets.prod.enc.env`, age key at `~/.config/sops/age/keys.txt`
- Edit secrets: `sops secrets/secrets.prod.enc.env`
- AWS (boto3) still used for S3 backups only, NOT for config/secrets

### Database Patterns

- SQLAlchemy 2.0 declarative base, `Mapped[type]` annotations
- Sessions via `create_session(settings)` context manager or FastAPI `Depends(get_sqlalchemy_session)`
- Pydantic schemas: `*Create` (POST), base (GET), `*Update` (PATCH, all optional), `ConfigDict(from_attributes=True)`
- Migrations: Alembic (`ichrisbirch/alembic/`). Run migrations before tests if schema changes.

## Testing

**Containerized**: Separate Docker Compose environment with isolated database and Redis, runs alongside dev on alternate ports.

**Python fixtures** (`tests/conftest.py`): Session-scoped (Docker orchestration, table lifecycle, test users), module-scoped (`test_api`, `test_api_logged_in`, `test_api_logged_in_admin`, `test_app`, `test_app_logged_in`), function-scoped (`*_function` suffix for isolation).

**Vue three-layer strategy**: `test:build` (TypeScript + Vite), `test:unit` (Vitest), `test:e2e` (Playwright through Traefik). E2E defaults to test containers; use `E2E_ENV=dev` for dev.

**Critical: Dev/Test vs Production Builds** — Dev and test use bind mounts (code from filesystem, not Docker image). Production uses `COPY . /app`. Docker build issues may NOT be caught in dev/test. Test prod builds with `icb prod build-test`.

## Deployment

Multi-stage Dockerfile: `base` → `development-builder` → `development` | `testing` | `production-builder` → `production`. Specify `--target`. Production image runs non-root with minimal deps.

Traefik dynamic config at `deploy-containers/traefik/dynamic/`. SSL certs managed via `./cli/ichrisbirch ssl-manager`.

## Conventions

### Must Follow

- **Pre-commit hooks** run automatically: Ruff, mypy, codespell, bandit, ESLint, Prettier, TypeScript checking, sass compile, and more. Vue hooks only trigger on `frontend/**/*.{vue,ts,tsx,js,jsx}`.
- **NEVER modify `sys.path`** — use standard imports. Use `find_project_root()` from `ichrisbirch.util` instead of `Path(__file__).parent.parent.parent`.
- **NEVER use `# noqa`** to bypass import order errors (E402). Restructure code instead.
- **Database columns**: Always use `Text`, never `String(n)` or `varchar`.
- **Categorical fields**: Use lookup tables with `TEXT PRIMARY KEY` + FK, never PostgreSQL enums.
- **Docker containers**: Prefixed `icb-{env}-{service}` (e.g., `icb-dev-api`).
- **Docker Compose overrides**: List fields (`ports`, `volumes`, `environment`) **merge by default** across compose files. When a test/dev compose redefines a list that exists in the base compose, use `!override` to replace instead of append (e.g., `ports: !override`). Without this, both port mappings apply and cause "port already allocated" errors.
- **File naming**: Lowercase with hyphens for docs (except README.md, CLAUDE.md, LICENSE.md). Snake_case for DB tables/columns.

### Adding a Vue Page

1. Create Pinia store with `createLogger`, `ApiError` handling, `error: ref<ApiError | null>`
2. Create Vue view with `<script setup>`, `onMounted` fetch, `useNotifications()` for feedback
3. Add route in `frontend/src/router.ts` (lazy-loaded)
4. Update sidebar in `AppSidebar.vue` (`migrated: true`)
5. Add PathPrefix to Traefik routing in **all three** compose files
6. Write unit tests (mock API with `vi.mock`) and E2E tests (Playwright through `app.docker.localhost`)

### Logging

**Python**: structlog with stdout-only. `LOG_FORMAT` (`console`/`json`), `LOG_LEVEL`, `LOG_COLORS` env vars. Request tracing via `X-Request-ID`.

**Vue**: consola with structured reporters matching structlog key=value format. JSON for Loki in production. Use `createLogger('ModuleName')`.

```bash
./cli/ichrisbirch dev logs [service]     # Dev logs
./cli/ichrisbirch testing logs [service] # Test logs
```

## Documentation

**Check docs first** before changing infrastructure, deployment, or migrations.

**Serve locally**: `mkdocs serve` → `http://127.0.0.1:8000`

Key docs: [Quick Start](docs/quick-start.md), [CLI Usage](docs/cli-traefik-usage.md), [Traefik Deployment](docs/traefik-deployment.md), [Alembic Migrations](docs/alembic.md), [Testing Guide](docs/testing/overview.md), [Troubleshooting](docs/troubleshooting.md)

**API docs**: FastAPI Swagger at `https://api.docker.localhost/docs`
