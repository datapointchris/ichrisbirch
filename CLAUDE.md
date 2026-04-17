# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

iChrisBirch is a personal productivity web application with a **multi-service architecture**: FastAPI backend (API), Vue 3 SPA frontend, Streamlit chat interface, and APScheduler service. All services share a PostgreSQL database and Redis cache, orchestrated via Docker Compose with Traefik reverse proxy.

**Package Management**: uv for Python (`uv.lock`), npm for Vue (`package-lock.json`)

## Essential Commands

```bash
# Development
./cli/icb dev start|stop|restart|rebuild|status|health|logs
./cli/icb dev rebuild --all          # Full rebuild including infra (traefik, postgres, redis)
./cli/icb dev rebuild --volumes      # Wipe named volumes and rebuild (stackable with --all)

# Testing (reuses containers, cleans database each run)
./cli/icb test run              # All tests (auto-starts containers if needed)
./cli/icb test run <path> -v    # Specific test (auto-starts containers if needed)
./cli/icb testing start|stop|health|logs  # Container management
./cli/icb testing rebuild --all      # Full rebuild including infra
./cli/icb testing rebuild --volumes  # Wipe named volumes and rebuild (use for ENOTEMPTY/crash-loop recovery)

# Database lifecycle (testing)
./cli/icb testing db init       # First-time: schemas + migrations + users
./cli/icb testing db reset      # Nuclear: drop + recreate everything

# Vue frontend
cd frontend && npm test                 # Build check + unit tests
cd frontend && npm run test:e2e         # Playwright E2E through Traefik

# Traefik routing (after adding a Vue page path)
./cli/icb routing generate

# Merged Docker Compose config (debug overrides)
./cli/icb dev docker config [service]
./cli/icb testing docker config [service]

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
- **Deployment**: Push to main triggers webhook → blue/green deploy with zero downtime. Logs at `/srv/ichrisbirch/logs/`
- **Blue/green**: Infrastructure (`icb-infra`) always running; app services alternate between `icb-blue`/`icb-green`. See `docs/blue-green-deployment.md`.

```bash
# View production logs (read-only SSH) — replace {color} with blue or green
ssh chris@10.0.20.11 "docker logs icb-blue-api --tail=50 2>&1"
ssh chris@10.0.20.11 "docker logs icb-blue-vue --tail=50 2>&1"
ssh chris@10.0.20.11 "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

# Check which color is active
ssh chris@10.0.20.11 "cat /var/lib/ichrisbirch/bluegreen-state"

# Webhook server logs (if containers never started)
ssh chris@10.0.20.15 "ls -lt /opt/webhooks/logs/ichrisbirch-*.log | head -5"
```

## Architecture

### Services

| Service | Framework | Purpose |
| --------- | ----------- | --------- |
| API | FastAPI | RESTful backend, JWT + Authelia auth |
| Vue | Vue 3 + TypeScript | SPA frontend (all pages) |
| Chat | Streamlit | AI chat interface with OpenAI |
| Scheduler | APScheduler | Daily jobs (task priorities, autotasks) |
| MCP | FastMCP | MCP tool server for Claude Code (streamable HTTP in prod, stdio in dev) |

Core directories: `ichrisbirch/` (Python backend), `frontend/` (Vue 3 SPA), `tests/` (Python test suite). See the filesystem for the full structure.

### Vue Frontend

Vue serves all pages. Flask was fully removed after all 14 pages were migrated.

**Key patterns:**

- Pinia stores with `ApiError`, structured logging via `createLogger()`, `error: ref<ApiError | null>`
- `useTheme` composable: OKLCH color themes, named themes (from `~/tools/theme/`), accent hue slider, 14 fonts
- E2E tests run through `app.docker.localhost` (not `vue.docker.localhost`) to catch CORS issues
- Self-hosted fonts in `frontend/public/fonts/` (woff2)

**Critical:** Every new Vue path or static asset path must be added to `deploy-containers/traefik/vue-paths.txt`, then run `ich routing generate` to update all three routing files (dev, test, prod).

**CORS gotcha:** Wildcard `Access-Control-Allow-Headers: *` does NOT work with `credentials: true` — list headers explicitly in Traefik CORS middleware config (including `X-Request-ID`). CORS and security headers are in separate middlewares to prevent chaining conflicts.

### Authentication

**Authelia (Production):** ForwardAuth on `ichrisbirch.com` routes, injects `Remote-User`/`Remote-Email` headers. `api.ichrisbirch.com` bypasses ForwardAuth (for JWT/API key clients like MCP tools). Config in `~/homelab`.

**Vue (Production):** Same-origin proxy — Vue calls `/api/...`, Traefik `api-proxy` router (priority 200) strips `/api` prefix and forwards to FastAPI. No CORS needed.

**Vue (Dev):** Cross-origin — Vue calls `https://api.docker.localhost` directly. Traefik `dev-authelia-sim` middleware injects `Remote-User: admin@icb.com`.

**FastAPI:** JWT tokens (access 15min, refresh 7d) + Authelia `Remote-User` header (highest priority) + Personal API Keys. Protected routes use `Depends(auth.get_current_user)`.

### Configuration & Secrets

- All environments use `.env` files (loaded via `python-dotenv`), set `ENVIRONMENT=development|testing|production`
- **Secrets**: SOPS + age — encrypted at `secrets/secrets.prod.enc.env`, age key at `~/.config/sops/age/keys.txt`
- Edit secrets: `sops secrets/secrets.prod.enc.env`
- AWS (boto3) still used for S3 backups only, NOT for config/secrets

### Database Patterns

- SQLAlchemy 2.0 declarative base, `Mapped[type]` annotations
- **Session pattern decision tree** — `create_session(settings)` requires explicit settings (no default):

  | Context | Pattern | Why |
  | --------- | --------- | ----- |
  | FastAPI routes | `Depends(get_sqlalchemy_session)` | DI wrapper calls `get_settings()` internally |
  | Scheduler jobs | `create_session(settings)` | Settings passed from job registration |
  | CLI / scripts | `create_session(get_settings())` | Caller owns the settings lookup |
  | Tests | Transactional fixtures (`test_settings`) | Session-scoped fixtures in `conftest.py` |

- Pydantic schemas: `*Create` (POST), base (GET), `*Update` (PATCH, all optional), `ConfigDict(from_attributes=True)`
- Migrations: Alembic (`ichrisbirch/alembic/`). Run migrations before tests if schema changes.

## Testing

**Containerized**: Separate Docker Compose environment with isolated database and Redis, runs alongside dev on alternate ports. `icb test run` **automatically starts containers** if they're not already running and waits for health checks — you never need to start them manually first. Test containers are **ephemeral** — the postgres data volume is destroyed on `testing stop`. If the test DB is in a broken state, the fix is `testing stop` then `testing start` (fresh DB with migrations). Never manually manipulate the test database with psql, alembic stamps, or raw SQL. If the CLI can't recover the DB, that's a CLI bug to fix.

**Test `.venv` is an anonymous Docker volume (matches dev/prod)** (⚠️ MANDATORY): The api/chat/scheduler services in `docker-compose.test.yml` mount `/app/.venv` as an anonymous volume (no `source:`), so Docker re-seeds it from the image layer on every new container. Commands are direct (`uvicorn`, `streamlit`, `python -m …`) — **never** `uv run` at container startup. An earlier named-volume setup (`venv_shared`, `uv_cache`) combined with `uv run` caused stale venv state to persist across rebuilds, producing API containers stuck in "health: starting" while uv tried to resync packages at runtime. Do not reintroduce named volumes for `.venv` or the uv cache in test, dev, or CI compose files — that architectural invariant is what makes the three environments behave the same way.

**If test containers still misbehave — wipe first, investigate second**: Even with anonymous `.venv` volumes, Docker can keep stale state in other named volumes (notably `icb-test-vue-node-modules`). Partial-install state in that volume (e.g., npm install interrupted mid-run) produces `ENOTEMPTY: directory not empty` errors in a restart loop that — if it runs long enough — can crash `dockerd` itself. Use the CLI flag FIRST:

```bash
./cli/icb testing rebuild --all --volumes   # down --volumes + rebuild all + up
# or for dev:
./cli/icb dev rebuild --all --volumes
```

Fallback when the CLI is wedged or docker itself has crashed (restart-looping vue container brought down the daemon):

```bash
sudo systemctl restart docker
docker rm -f icb-test-vue 2>/dev/null     # kill the loop before restart policy puts docker back in the same state
docker volume rm icb-test-vue-node-modules 2>/dev/null
docker ps -a --filter "name=icb-test" -q | xargs -r docker rm -f
docker volume ls --filter "name=icb-test" -q | xargs -r docker volume rm
docker network ls --filter "name=icb-test" -q | xargs -r docker network rm
./cli/icb testing start
```

Do not edit the Dockerfile, compose files, or add entrypoint scripts to "fix" state problems. If fresh containers from a clean wipe still fail, THEN investigate.

**Bind mount + named volume overlap creates root-owned empty host dirs** (expected, not a bug): The vue services mount `./frontend:/app` (bind) AND `vue_*_node_modules:/app/node_modules` (named volume). Docker needs `./frontend/node_modules/` to exist on the host as a mount point — if it doesn't, the Docker daemon auto-creates it, which means `root:root` ownership. At runtime the named volume shadows it, so container writes go to the volume, NOT the host directory. Host-side `npm install` writes are therefore invisible to the container. Don't try to "fix" the ownership in compose — either accept the empty host dir, or `mkdir frontend/node_modules` as your user BEFORE bringing up containers if you need host-side node_modules for pre-commit typecheck.

**Dual iptables backends can block Docker egress** (Arch gotcha): If containers on a NEWER Docker network can ping their gateway but not the internet, while older networks work fine, the cause is orphan `iptables-legacy` rules referencing dead bridge IDs. The Linux kernel loads both netfilter backends simultaneously and evaluates both; Docker only maintains rules in its current backend (nft). Diagnose: `sudo iptables-legacy -t nat -L POSTROUTING -n -v` — stale bridge IDs are the signal. Recovery: `sudo iptables-legacy -F && sudo iptables-legacy -t nat -F && sudo systemctl restart docker`. See `project_docker_iptables_gotcha.md` in memory for full forensics.

**Python fixtures** (`tests/conftest.py`): Session-scoped (Docker orchestration, table lifecycle, test users), module-scoped (`test_api`, `test_api_logged_in`, `test_api_logged_in_admin`), function-scoped (`*_function` suffix for isolation).

**Vue four-layer strategy**: `test:build` (TypeScript + Vite), `test:unit` (Vitest store/composable tests), `test:component` (Vitest + `@pinia/testing` view integration tests), `test:e2e` (Playwright through Traefik). E2E tests ALWAYS run against test containers, never dev.

**Component integration tests** (`frontend/src/views/__tests__/`): Mount real Vue components with `createTestingPinia({ initialState, stubActions: true, createSpy: vi.fn })`. Verify rendering, conditional CSS classes, store action wiring, and modal props. Stub child components (modals, subnavs) and mock composables (`useNotifications`, `formatDate`). These run in ~2s and cover behavior that E2E previously tested.

**E2E smoke-only pattern**: E2E tests are trimmed to smoke-level — each page keeps: CORS/API check, page load, sidebar nav, one CRUD roundtrip. Interaction-heavy tests (edit modals, toggles, filters, search) live in component tests. Every E2E file has a comment pointing to its component test counterpart.

**E2E assertion style**: Never assert on exact notification/log text (e.g., `toContainText('Duration added')`). Messages change format frequently and couple tests to implementation details. Assert on generic keywords that verify intent: `'added'`, `'deleted'`, `'completed'`. Test behavior, not message formatting.

**E2E selectors — use `data-testid`**: Never couple tests to CSS class names or DOM structure. Use `data-testid` attributes on interactive elements and `page.getByTestId()` in tests. This decouples tests from styling changes. Naming convention: `{entity}-{element}` — e.g., `countdown-add-button`, `countdown-name-input`, `countdown-item`, `add-edit-modal`. The `data-testid` attributes ship to production (negligible cost, enables prod E2E if needed).

**Critical: Dev/Test vs Production Builds** — Dev and test use bind mounts (code from filesystem, not Docker image). Production uses `COPY . /app`. Docker build issues may NOT be caught in dev/test. Test prod builds with `icb prod build-test`.

**Test output files** (written on every pytest run — pre-commit and CLI):

- `/tmp/ichrisbirch-pytest-output.log` — full terminal output (human-readable)
- `/tmp/ichrisbirch-pytest-report.json` — structured JSON report with nodeids, tracebacks, durations

When tests fail, read these files instead of re-running tests. The JSON report's `tests` array has `nodeid`, `outcome`, and `call.longrepr` (full traceback) for each failure.

**Vue test container `node_modules`** — The test Vue container uses a **named Docker volume** (`vue_test_node_modules`) for `node_modules`, not a bind mount. The container runs `npm install && npm run dev` on startup. When new npm packages are added to `package.json`, the running container won't have them — you must `testing stop` then `testing start` to trigger a fresh `npm install`. Same applies to DB schema changes (migrations run on startup). Symptoms: 500 errors on pages that import the new package, while other pages work fine.

## Deployment

Multi-stage Dockerfile: `base` → `development-builder` → `development` | `testing` | `production-builder` → `production`. Specify `--target`. Production image runs non-root with minimal deps.

**Production uses blue/green deployment** with zero downtime. Infrastructure (`docker-compose.infra.yml`) is always running. App services (`docker-compose.app.yml`) deploy as alternating blue/green projects. Traefik file provider: `routing.yml` (git-tracked routers) + `services.yml` (generated, points to active color). Database migrations must be backward-compatible. See `docs/blue-green-deployment.md`.

Traefik dynamic config at `deploy-containers/traefik/dynamic/`. Routing is generated from `deploy-containers/traefik/vue-paths.txt` via `ich routing generate`. CORS and security headers are separate middlewares per environment (`cors-*` and `security-headers-*`). Use `ich {dev,testing,prod} docker config [service]` to see fully merged compose output. SSL certs managed via `./cli/icb ssl-manager`.

## Conventions

### Must Follow

- **Pre-commit hooks** run automatically: Ruff, mypy, codespell, bandit, ESLint, Prettier, TypeScript checking, and more. Vue hooks only trigger on `frontend/**/*.{vue,ts,tsx,js,jsx}`.
- **Pre-commit "files were modified" failures**: When pre-commit reports `devstats capture...Failed - files were modified by this hook`, devstats is NOT the cause (its output is gitignored). The actual culprit is a later hook: `generate-fixture-diagrams` regenerating SVGs (triggered by `tests/conftest.py` or `mkdocs_plugins/diagrams/` changes), `ruff-check` auto-fixing code, or similar. Stage the generated files with `git add` and retry.
- **NEVER modify `sys.path`** — use standard imports. Use `find_project_root()` from `ichrisbirch.util` instead of `Path(__file__).parent.parent.parent`.
- **NEVER use `# noqa`** to bypass import order errors (E402). Restructure code instead.
- **Database columns**: Always use `Text`, never `String(n)` or `varchar`.
- **Categorical fields**: Use lookup tables with `TEXT PRIMARY KEY` + FK, never PostgreSQL enums.
- **Docker containers**: Prefixed `icb-{env}-{service}` (e.g., `icb-dev-api`). Production uses `icb-infra-{service}` for infrastructure and `icb-{blue|green}-{service}` for app services.
- **Docker Compose overrides**: List fields (`ports`, `volumes`, `environment`) **merge by default** across compose files. When a test/dev compose redefines a list that exists in the base compose, use `!override` to replace instead of append (e.g., `ports: !override`). Without this, both port mappings apply and cause "port already allocated" errors.
- **File naming**: Snake_case for DB tables/columns. (Markdown naming: see global CLAUDE.md.)

### Styling & Design Cohesion

**Global over scoped**: Use the shared SCSS system (`frontend/src/assets/sass/`) for visual styling. Avoid duplicating shadow/effect/button styles in Vue scoped `<style>` blocks — scoped overrides create maintenance burden and drift from the site's visual language. Scoped styles should handle layout (flexbox, grid, spacing) not visual effects.

**Neumorphic shadow vocabulary** (defined in `layout/_grid.scss`):

- `--floating-box`: raised/resting state (cards, rows, nav links)
- `--floating-box-pressed`: sunken/active state (selected items, pressed buttons)
- `--bubble-box` / `--bubble-box-pressed`: hover states (lighter raise/press)

**Shared SCSS mixins** (`components/`): Compound mixins following the `search-results` pattern — consumers include at entity level and set `grid-template-columns`. Mixins are opinionated (define the full visual pattern); consumers only provide what genuinely varies.

- `data-table` — flat grid table with header/row/cell/actions (Articles, Money Wasted)
- `card-row` — neumorphic raised row with title/link/actions/chevron (Books, Box Packing compact)
- `list-item` — bordered row with hover highlight and last-child cleanup (Habits, Box contents, Duration notes)

**Empty-state convention**: All `{block}__empty` classes use exactly `color: var(--clr-gray-500); font-style: italic` — no padding, font-size, or display overrides. Empty states inherit layout from their container.

**`double-bevel-button` mixin** (`components/_buttons.scss`): Circular neumorphic buttons with inner button + outer ring. Takes `$button-size` — everything else (outer ring at 1.5x, icon at 30% via `$content-ratio`, `position: relative`) is calculated automatically. Never override proportions per-caller.

**Proportional sizing**: Buttons, icons, and text within shared components must scale proportionally from a single size parameter. Never use fixed font sizes inside scaled containers.

**Design-style-switch readiness** (⚠️ MANDATORY): The site is being built toward a future design style switcher (neumorphic / jagged / bubbly / etc.) that changes shape, shadow, and border properties site-wide — the same way the color theme switcher changes all colors today. To keep this feasible:

- **NEVER** hardcode `box-shadow`, `border-radius`, or button shapes in scoped `<style>` blocks. Always reference the CSS variable (`--floating-box`, `--border-radius`, etc.).
- **NEVER** hardcode chart colors, grid colors, or text colors in Chart.js config. Use `getThemeColors()` / `paletteColors()` from `useStatsCharts` composable, which reads live CSS custom properties.
- All visual effects must flow through CSS variables defined in the SCSS abstracts layer. Scoped styles handle **layout only** (flexbox, grid, gaps, padding).
- When the switcher is built, it will toggle a `data-design` attribute on `<html>` and swap variable sets. Components that follow these rules will just work.

**Stats page shared kit** (`frontend/src/components/stats/`, `frontend/src/composables/useStatsCharts.ts`): Reusable components for any entity's stats/analytics page. `StatsSummaryCards` (value + label card row), `StatsTable` + `StatsTableRow` (header + neumorphic rows), `useStatsCharts` (theme-aware Chart.js colors and option builders). All chart colors are derived from the active theme's CSS custom properties (`--clr-accent`, `--clr-secondary`, `--clr-tertiary`, `--clr-info`, `--clr-warning`, `--clr-success`).

### Component Architecture — Consistency Over Convenience

**Every reusable pattern gets a wrapper per entity.** When a shared component exists (e.g., `AddEditModal`), every entity that uses it gets its own wrapper component (e.g., `AddEditTaskModal`, `AddEditCountdownModal`). The wrapper encapsulates all entity-specific form markup, state, and validation. The page just drops in the component with one line and handles the emitted event. No exceptions based on form complexity — a 2-field form gets a wrapper the same as a 10-field form.

**No subjective "rule of thumb" thresholds.** Either ALL pages follow the pattern or NONE do. This applies to components, composables, shared SCSS, and any architectural pattern. Consistency makes the codebase predictable — the next developer knows exactly where to find things and how to add new pages.

### Adding a New API Endpoint (⚠️ MANDATORY checklist)

Every new API endpoint group **must** include a seeder script. No exceptions.

1. Create SQLAlchemy model + Alembic migration
2. Create Pydantic schemas (Create, response, Update)
3. Create FastAPI router in `ichrisbirch/api/endpoints/`
4. Register router in `ichrisbirch/api/main.py`
5. **Create seeder in `scripts/seed/seeders/<name>.py`** — implements `seed(session, scale)` and `clear(session)`, returns `SeedResult`
6. **Register seeder in `scripts/seed/seeders/__init__.py`** — add to import list and `SEED_ORDER` (after its FK dependencies)
7. Create test data in `tests/test_data/<name>.py` + register in `tests/test_data/__init__.py`
8. Write API endpoint tests in `tests/ichrisbirch/api/endpoints/test_<name>.py`

### Adding a Stats Page

Follow the Articles/Tasks stats pattern. Every stats page uses the shared kit.

1. **Backend**: Add stats Pydantic schemas to `ichrisbirch/schemas/<entity>.py` (SummaryStats, per-category/tag breakdown, time-series, notable items list) + export from `schemas/__init__.py`
2. **Backend**: Add `GET /<entity>/stats/` endpoint with DB-level aggregation (use `func.count`, `func.avg`, `func.date_trunc`, `extract`). Place before `/{id}/` routes.
3. **Frontend types**: Add TypeScript interfaces to `frontend/src/api/types.ts` + export from `client.ts`
4. **Frontend view**: Create `<Entity>StatsView.vue` — import `StatsSummaryCards`, `StatsTable`, `StatsTableRow`, and chart builders from `useStatsCharts`. All chart colors via `getThemeColors()` / `paletteColors()`.
5. **Route**: Add to `frontend/src/router.ts` (before parent route if it has path params)
6. **Subnav**: Add Stats link to the entity's subnav component
7. **Seed data**: Ensure the entity's seeder produces enough varied data to make charts meaningful (spread dates, varied categories, mix of completed/outstanding)

### Adding a Vue Page

1. Create Pinia store with `createLogger`, `ApiError` handling, `error: ref<ApiError | null>`
2. Create Vue view with `<script setup>`, `onMounted` fetch, `useNotifications()` for feedback
3. Add route in `frontend/src/router.ts` (lazy-loaded)
4. Update sidebar in `AppSidebar.vue`
5. Add path to `deploy-containers/traefik/vue-paths.txt` and run `ich routing generate`
6. Write unit tests (mock API with `vi.mock`) and E2E tests (Playwright through `app.docker.localhost`)

### Logging

**Python**: structlog with stdout-only. `LOG_FORMAT` (`console`/`json`), `LOG_LEVEL`, `LOG_COLORS` env vars. Request tracing via `X-Request-ID`.

**Vue**: consola with structured reporters matching structlog key=value format. JSON for Loki in production. Use `createLogger('ModuleName')`.

```bash
./cli/icb dev logs [service]     # Dev logs
./cli/icb testing logs [service] # Test logs
```

## Documentation

**Check docs first** before changing infrastructure, deployment, or migrations.

**Serve locally**: `mkdocs serve` → `http://127.0.0.1:8000`

Key docs: [Quick Start](docs/quick-start.md), [CLI Usage](docs/cli-traefik-usage.md), [Blue/Green Deployment](docs/blue-green-deployment.md), [Traefik Deployment](docs/traefik-deployment.md), [Alembic Migrations](docs/alembic.md), [Testing Guide](docs/testing/overview.md), [Troubleshooting](docs/troubleshooting.md)

**API docs**: FastAPI Swagger at `https://api.docker.localhost/docs`
