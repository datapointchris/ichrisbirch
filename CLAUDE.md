# CLAUDE.md

## Project Overview

iChrisBirch is a personal productivity web application: a FastAPI backend, a Vue 3 SPA and an APScheduler service, sharing PostgreSQL and Redis behind Traefik and orchestrated with Docker Compose.

`./ops/icbops --help` is the command surface for dev, testing, database, routing and production. Dev is `https://app.docker.localhost/` with the API at `https://api.docker.localhost/`; tests run against `https://api.test.localhost:8443/`.

## Production Environment

**Production runs on a self-hosted server, NOT locally.**

- **Application host**: installed at `/srv/ichrisbirch/`, logs at `/srv/ichrisbirch/logs/`
- **Webhook host**: receives the push notification and runs the deploy; logs at `/opt/webhooks/logs/`
- **Deployment**: Push to main triggers the webhook → blue/green deploy with zero downtime
- **Blue/green**: Infrastructure (`icb-infra`) always running; app services alternate between `icb-blue`/`icb-green`. See `docs/blue-green-deployment.md`.

The two hosts are named by `$ICB_PROD_HOST` and `$ICB_WEBHOOK_HOST`, which each
operator sets for their own deployment. Reading logs and container status over
SSH is fine; anything that changes production goes through the deploy pipeline.
The active color is in `/var/lib/ichrisbirch/bluegreen-state` on the application host.

## Architecture

### CLIs — `icbops` (ops) and `icb` (data)

- **`ops/icbops`** — the bash ops/deploy tool (`dev`/`test`/`docker`/`routing`/`ssl-manager`/`db`/`stats`/`logs`). Path-invoked as `./ops/icbops <cmd>`; `icbops install` symlinks it to `~/.local/bin/icbops`. This is the tool used throughout this doc for local dev, testing, and deploy operations.
- **`cli/`** — the `icb` Go/cobra resource CLI: a thin REST client over the FastAPI and the programmatic data surface (`icb <resource> <verb>`, `--json` on reads). It is its own Go module (`github.com/datapointchris/ichrisbirch/cli`). `cli/README.md` covers build, install and auth, along with the guided-create form (`internal/prompt`) and the `[]prompt.Field` pattern any resource with a closed vocabulary should follow. The Authelia client ids (`icb-cli-<host>`) and the keyring service name (`icb-cli`) are deployed identifiers and keep the old spelling — they are not path-derived.

### Vue Frontend

- Pinia stores with `ApiError`, structured logging via `createLogger()`, `error: ref<ApiError | null>`
- `useTheme` composable: OKLCH color themes, named themes, accent hue slider, font choice
- Self-hosted fonts in `frontend/public/fonts/` (woff2)

**Critical:** Every new Vue path or static asset path must be added to `deploy-containers/traefik/vue-paths.txt`, then run `icbops routing generate` to update all three routing files (dev, test, prod).

**CORS gotcha:** Wildcard `Access-Control-Allow-Headers: *` does NOT work with `credentials: true` — list headers explicitly in Traefik CORS middleware config (including `X-Request-ID`). CORS and security headers are in separate middlewares to prevent chaining conflicts.

### Authentication

**Authelia (Production):** ForwardAuth on `ichrisbirch.com` routes, injects `Remote-User`/`Remote-Email` headers for browser sessions. `api.ichrisbirch.com` bypasses ForwardAuth for every request — that is the Personal API Key path, and it is being retired along with those clients. The `icb` CLI does not use it: the `ichrisbirch-bearer` router carries a request holding an `Authorization` header past ForwardAuth, so the CLI targets `ichrisbirch.com/api` and only bearer requests skip the edge. `cli/internal/config/config.go` sets that as `defaultAPIBase`.

**OIDC bearer (the `icb` CLI):** the CLI logs in with the device authorization grant, so its access token is an RFC 9068 JWT rather than an edge-authorized opaque token. `ichrisbirch/api/oidc_auth.py` verifies it in-process with PyJWT's `PyJWKClient`: header `typ` is `at+jwt`, RS256 signature against Authelia's JWKS, `iss` matches, `sub` non-empty, `client_id` starts with `icb-cli-`, `exp` in the future. Authelia does not carry the audience through the device grant, so `aud` is empty and the `client_id` prefix is what keeps another product's token out. Every rejection returns one opaque 401, and a presented-but-invalid access token never falls through to a weaker strategy.

**Login and token lifecycle belong to `github.com/datapointchris/goclilogin`**; the CLI holds only the mapping in `config.Config.Login()`, so do not reintroduce an `internal/auth` here.

The mapping passes `StateDir` explicitly rather than taking goclilogin's default, which would resolve under the keyring service name. That directory holds the refresh lock and the mode-600 token file used where there is no OS keyring. Released versions of `icb` already write `$XDG_STATE_HOME/icb/<client_id>.refresh.lock`, and two versions naming different lock files would not exclude each other during an upgrade.

**Vue (Production):** Same-origin proxy — Vue calls `/api/...`, Traefik `api-proxy` router (priority 200) strips `/api` prefix and forwards to FastAPI. No CORS needed.

**Vue (Dev):** Cross-origin — Vue calls `https://api.docker.localhost` directly. Traefik `dev-authelia-sim` middleware injects `Remote-User: admin@icb.com`.

**FastAPI:** verified Authelia OIDC access tokens (highest priority) + Authelia `Remote-User` header + Personal API Keys + local JWT tokens (access 15min, refresh 7d). Protected routes use `Depends(auth.get_current_user)`.

### Configuration & Secrets

- Every environment loads a `.env` file via `python-dotenv` and sets `ENVIRONMENT=development|testing|production`
- Secrets are SOPS + age, encrypted at `secrets/secrets.prod.enc.env`; edit with `sops secrets/secrets.prod.enc.env`
- AWS (boto3) is used for S3 backups only, NOT for config or secrets

### Outbound HTTP Goes Through One Function

Fetching a page from a third party is `get_page` in
`ichrisbirch/services/outbound_http.py`. It sends a real browser's TLS fingerprint
through `curl_cffi`, follows redirects, applies a 60-second timeout and returns a
`FetchedPage`. Sites behind bot protection refuse a plain HTTP client whatever user
agent it claims. Never fetch an outside URL any other way; add the case to
`get_page` instead.

Turning a saved URL into a title and text is `read_article_page` in
`services/url_extraction.py`, used by the article endpoints, the bulk import worker
and recipe import. It refuses a redirect to the homepage, a bot check and a page
with too little text, each as its own exception.

Two callers are deliberately outside it, because they are not third-party
page fetches:

- **`api/oidc_auth.py`** — OIDC discovery against the identity provider, with its
  own user agent and a caller-supplied timeout.
- **`gui/`** — posts to this app's own endpoints.

Two subprocesses are sanctioned: the one in `scheduler/jobs.py`, and the Claude
Code CLI that `claude-agent-sdk` starts for each call from
`ai/assistants/anthropic.py`.

### What a Dependency Can Reach

`docs/dependency-reach.md` records what each wide-reaching dependency sees; a new one that receives user content, makes outbound requests or touches the host gets an entry there.
The Claude Code CLI that `claude-agent-sdk` starts inherits the API's whole decrypted `.env`, and that is accepted.
`options()` blanks `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` on every call, because either outranks the subscription token inside Claude Code and usage must draw on the plan, never API credits.

**One driver, not two.** `psycopg` (3) is what the connection URL names (`postgresql+psycopg://`); anything in the docs spelling an error `psycopg2.*` predates it.

### Database Patterns

- SQLAlchemy 2.0 declarative base, `Mapped[type]` annotations
- **Session pattern decision tree** — `create_session(settings)` requires explicit settings (no default):

  | Context | Pattern | Why |
  | --- | --- | --- |
  | FastAPI routes | `Depends(get_sqlalchemy_session)` | DI wrapper calls `get_settings()` internally |
  | Scheduler jobs | `create_session(settings)` | Settings passed from job registration |
  | CLI / scripts | `create_session(get_settings())` | Caller owns the settings lookup |
  | Tests | Transactional fixtures (`test_settings`) | Session-scoped fixtures in `conftest.py` |

- Pydantic schemas: `*Create` (POST), base (GET), `*Update` (PATCH), `ConfigDict(from_attributes=True)`. Every `*Update` field may be omitted. A field over a NOT NULL column is written `NotNull[T] = None` (`schemas/not_null.py`), so an explicit null answers 422 rather than reaching the column as a 500. `test_update_schemas_refuse_null.py` walks every `*Update` against its model and fails on one that lets a null through.
- Migrations: Alembic (`ichrisbirch/alembic/`). A migration creates any schema it writes into, as `e1f2a3b4c5d6_add_coffee_tables` does, because nothing creates schemas ahead of alembic. pytest's session setup migrates the test database to head.

## Testing

**Containerized**: Separate Docker Compose environment with isolated database and Redis, runs alongside dev on alternate ports. `icbops test run` **automatically starts containers** if they're not already running and waits for health checks — you never need to start them manually first. Test containers are **ephemeral** — the test Postgres keeps its data on tmpfs, so every stop or recreate of that container empties the database. Every verb that brings the test containers up (`testing start`, `testing restart`, `testing rebuild` with any flags, and `test run`'s cold start) ends by initializing the database, and pytest's session setup migrates it to head before its fixtures truncate it, so a healthy container over an empty database still runs the suite. If the test DB is in a broken state, the fix is `testing stop` then `testing start` (fresh DB with migrations). Never manually manipulate the test database with psql, alembic stamps, or raw SQL. If the CLI can't recover the DB, that's a CLI bug to fix.

**Test `.venv` is an anonymous Docker volume (matches dev/prod)** (⚠️ MANDATORY): The api/scheduler services in `docker-compose.test.yml` mount `/app/.venv` as an anonymous volume (no `source:`), so Docker re-seeds it from the image layer on every new container. Commands are direct (`uvicorn`, `python -m …`) — **never** `uv run` at container startup. A named volume for `.venv` or the uv cache, combined with `uv run`, keeps stale venv state across rebuilds and leaves the API stuck in "health: starting" while uv resyncs at runtime. Do not reintroduce named volumes for `.venv` or the uv cache in test, dev, or CI compose files — that architectural invariant is what makes the three environments behave the same way.

**If test containers still misbehave — wipe first, investigate second**: Even with anonymous `.venv` volumes, Docker can keep stale state in other named volumes (notably `icb-test-vue-node-modules`). Partial-install state in that volume (e.g., npm install interrupted mid-run) produces `ENOTEMPTY: directory not empty` errors in a restart loop that — if it runs long enough — can crash `dockerd` itself. Use the CLI flag FIRST:

```bash
./ops/icbops testing rebuild --all --volumes   # down --volumes + rebuild all + up + initialize the database
# or for dev:
./ops/icbops dev rebuild --all --volumes
```

Fallback when the CLI is wedged or docker itself has crashed (restart-looping vue container brought down the daemon):

```bash
sudo systemctl restart docker
docker rm -f icb-test-vue 2>/dev/null     # kill the loop before restart policy puts docker back in the same state
docker volume rm icb-test-vue-node-modules 2>/dev/null
docker ps -a --filter "name=icb-test" -q | xargs -r docker rm -f
docker volume ls --filter "name=icb-test" -q | xargs -r docker volume rm
docker network ls --filter "name=icb-test" -q | xargs -r docker network rm
./ops/icbops testing start
```

Do not edit the Dockerfile, compose files, or add entrypoint scripts to "fix" state problems. If fresh containers from a clean wipe still fail, THEN investigate.

**Bind mount + named volume overlap creates root-owned empty host dirs** (expected, not a bug): The vue services mount `./frontend:/app` (bind) AND `vue_*_node_modules:/app/node_modules` (named volume). Docker needs `./frontend/node_modules/` to exist on the host as a mount point — if it doesn't, the Docker daemon auto-creates it, which means `root:root` ownership. At runtime the named volume shadows it, so container writes go to the volume, NOT the host directory. Host-side `npm install` writes are therefore invisible to the container. Don't try to "fix" the ownership in compose — either accept the empty host dir, or `mkdir frontend/node_modules` as your user BEFORE bringing up containers if you need host-side node_modules for pre-commit typecheck.

**Python fixtures** (`tests/conftest.py`): Session-scoped (Docker orchestration, table lifecycle, test users), module-scoped (`test_api`, `test_api_logged_in`, `test_api_logged_in_admin`), function-scoped (`*_function` suffix for isolation).

**Vue test layers**: `test:build` (TypeScript + Vite), `test:unit` (Vitest — store/composable tests *and* the `@pinia/testing` view integration tests; one script covers both layers), `test:e2e` (Playwright through Traefik). E2E tests ALWAYS run against test containers, never dev.

**Component integration tests** (`frontend/src/views/__tests__/`): Mount real Vue components with `createTestingPinia({ initialState, stubActions: true, createSpy: vi.fn })`. Verify rendering, conditional CSS classes, store action wiring, and modal props. Stub child components (modals, subnavs) and mock composables (`useNotifications`, `formatDate`).

**E2E smoke-only pattern**: E2E tests are trimmed to smoke-level — each page keeps: CORS/API check, page load, sidebar nav, one CRUD roundtrip. Interaction-heavy tests (edit modals, toggles, filters, search) live in component tests. Every E2E file has a comment pointing to its component test counterpart.

**E2E assertion style**: Never assert on exact notification/log text (e.g., `toContainText('Duration added')`). Messages change format frequently and couple tests to implementation details. Assert on generic keywords that verify intent: `'added'`, `'deleted'`, `'completed'`. Test behavior, not message formatting.

**E2E selectors — use `data-testid`**: Never couple tests to CSS class names or DOM structure. Use `data-testid` attributes on interactive elements and `page.getByTestId()` in tests. This decouples tests from styling changes. Naming convention: `{entity}-{element}` — e.g., `countdown-add-button`, `countdown-name-input`, `countdown-item`, `add-edit-modal`. The `data-testid` attributes ship to production (negligible cost, enables prod E2E if needed).

**Critical: Dev/Test vs Production Builds** — Dev and test use bind mounts (code from filesystem, not Docker image). Production uses `COPY . /app`. Docker build issues may NOT be caught in dev/test. Test prod builds with `icbops prod build-test`.

**Test output files**: every pytest run, from pre-commit or the CLI, writes `/tmp/ichrisbirch-pytest-output.log` (terminal output) and `/tmp/ichrisbirch-pytest-report.json` (whose `tests` array holds `nodeid`, `outcome` and `call.longrepr` per test). When tests fail, read these instead of re-running.

**Vue test container `node_modules`** — The test Vue container uses a **named Docker volume** (`vue_test_node_modules`) for `node_modules`, not a bind mount. The container runs `npm install && npm run dev` on startup. When new npm packages are added to `package.json`, the running container won't have them — you must `testing stop` then `testing start` to trigger a fresh `npm install`. Symptoms: 500 errors on pages that import the new package, while other pages work fine. A new migration reaches pytest without a restart, because its session setup migrates the test database to head. The API container still needs step 1 of the escalation ladder to load changed models.

## Deployment

The Dockerfile is multi-stage (`base` → `development` | `testing` | `production`), so always pass `--target`; the production image runs non-root.
Production is blue/green: `docker-compose.infra.yml` always runs, `docker-compose.app.yml` deploys as alternating colors, and Traefik reads the git-tracked `routing.yml` plus a generated `services.yml` pointing at the active color. Migrations must be backward-compatible. `docs/blue-green-deployment.md` § "Unsafe Operations" lists the changes that take two deploys, and a column's type is one of them: it changes through a new column, never in place.
Traefik dynamic config is `deploy-containers/traefik/dynamic/`, generated from `vue-paths.txt` by `icbops routing generate`, with CORS and security headers as separate middlewares per environment. `icbops {dev,testing,prod} docker config [service]` prints the merged compose; `./ops/icbops ssl-manager` manages certificates.

## Conventions

### `icb` CLI — dev vs prod (data access)

The `icb` CLI is the programmatic data surface. The installed binary is **not** repo-aware: it always targets **production** (`https://ichrisbirch.com/api`, Authelia OIDC bearer token) regardless of the working directory. So `icb tasks list` from inside this repo reads **prod**, not the local dev stack.

To read or write the **local dev** stack, hit the dev API directly (it injects `Remote-User` via the `dev-authelia-sim` middleware, so no token is needed): `curl -sk https://api.docker.localhost/tasks/`. Override the CLI's target per-invocation with `ICB_API_BASE` if you need `icb` itself pointed at dev.

### Always "Cooking Technique", never the bare word "technique"

`CookingTechnique`, `cooking_technique`, `cooking-techniques` — the full noun at every layer, in the model, the route, the URL and the prose. The bare word is too generic: "technique" alone reads as a name for anything.

Cooking techniques are part of the Recipes domain and not a separate entity, so the code lives inside the recipes files at every layer — `models/recipe.py` holds the model, and the routes hang under `/recipes/` in `api/endpoints/recipes.py`.

### Must Follow

- **Container code-change escalation ladder** (⚠️ MANDATORY): When edits aren't taking effect in running containers — new/renamed API routes, new dependencies, migrations, schema changes, Vue package.json changes, Python imports — follow THIS sequence in order. Do NOT skip steps. Do NOT substitute manual `docker` subcommands for these CLI steps:
  1. **`./ops/icbops testing stop && ./ops/icbops testing start`** (~30s). Fixes most issues — accumulated DB state, FastAPI not having re-registered routes, stale module imports. Test containers are ephemeral and should be killed freely.
  2. **`./ops/icbops testing rebuild --volumes`** (~60–90s). Use if step 1 didn't resolve it. Fixes stale `.venv` contents, dependency changes (pyproject.toml additions), anonymous-volume staleness, ENOTEMPTY errors, vue node_modules corruption.
  3. **ONLY NOW** reach for `docker logs`, `docker inspect`, `docker exec`, `docker restart`, or any manual docker subcommand. Fresh containers from step 2 still failing is a real bug; containers that haven't been through steps 1–2 aren't.

  The same ladder applies to dev via `./ops/icbops dev stop && start` then `./ops/icbops dev rebuild --volumes`. Doing `docker logs` / `docker exec` / `docker restart` BEFORE exhausting steps 1–2 is the single biggest time-waster in this workflow. If you catch yourself about to type `docker ` anything, STOP and check: have both steps 1 and 2 run since the code edit? If not, do them first.

  Ten manual docker subcommands — `exec`, `restart`, `logs`, `images`, `image inspect`, `run --rm`, `volume ls`, `inspect --format` and a `sudo ls` on a volume path — once failed to diagnose what step 2 with `--volumes` then fixed in 90 seconds. Each one feels like progress and all of it is archaeology. The tell that it has gone wrong is proposing a workaround rather than an escalation: baking the venv into the image is a workaround, and the ladder is the escalation.
- **Pre-commit config is generated.** `.pre-commit-config.yaml` and `.github/workflows/validate.yml` carry a `# forge-toolchain:` stamp; hand edits belong in a `# > custom:` block, which regeneration preserves. Vue hooks trigger only on `frontend/**/*.{vue,ts,tsx,js,jsx}`.
- **Pre-commit "files were modified" failures**: When pre-commit reports `devstats capture...Failed - files were modified by this hook`, devstats is NOT the cause (its output is gitignored). The actual culprit is a later hook: `generate-fixture-diagrams` regenerating SVGs (triggered by `tests/conftest.py` or `mkdocs_plugins/diagrams/` changes), `ruff-check` auto-fixing code, or similar. Stage the generated files with `git add` and retry.
- **A time column is one of three kinds, and the kind decides the type**: pick before writing the column, because all three are spelled `datetime` in Python and only one of them should be.
  1. **A moment that happened** — a completion, a login, a row appearing. `DateTime(timezone=True)`, written as `datetime.now(UTC)`, `server_default=func.now()`, or `pendulum.now()`. Never bare `datetime.now()`: naive is interpreted using Postgres's session `TimeZone`, so it is correct only while every container happens to run UTC. The three accepted forms all carry an offset, which is the property that matters; `pendulum.now()` carries the machine's zone rather than UTC and is correct for the same reason. Its request field is `AwareDatetime`, which refuses a reading with no offset.
  2. **A calendar day** — a purchase date, a day a habit was done, a due date. `Date`. Not a timestamp: a `YYYY-MM-DD` arriving as a timestamp becomes midnight UTC, and every reader west of UTC then renders the day before. Its request field is `date`.
  3. **A future local wall clock** — an event at a venue. Naive `DateTime(timezone=False)` plus a `Text` column holding the IANA zone name, and every reader resolves the pair before comparing it against anything. Storing an instant is wrong here, because a tzdata change moves it and because 19:00 at the venue is 19:00 for every reader. `events.date` plus `events.timezone` is the one pair, and `useWallClock` / `api.EventInstant` are the resolvers every reader goes through. Its request fields are `WallClock` and `IanaZone` (`schemas/wall_clock.py`, `schemas/iana_zone.py`).

  `test_time_fields_match_their_columns.py` walks every `*Create` and `*Update` against its model and fails on a field of the wrong kind, and on a naive column other than `events.date`.
- **Which day an instant falls on is read in the user's zone, never in UTC or the container's.** The user's zone is the `timezone` preference, which the web app fills from the browser for a user with none; `User.calendar_zone` answers UTC only before that.
  - **API**: a bound with no offset on a timestamp column, a bare day or a time, is read in `RequestZone` (`api/request_zone.py`) — the `timezone` query parameter when the caller sends one, else `User.calendar_zone`. `apply_date_bounds` takes the zone as a required keyword, and raises `TypeError` on such a bound when it is `None`. `test_date_bounded_reads.py` walks the routes and fails on a bounded read that does not declare `RequestZone`, unless `DAY_COLUMN_READS` names it with its `Date` column.
  - **Vue**: every instant is shown in `displayZone()`, and "today" is read there. Day arithmetic goes through `calendarDay.ts`, and the shared date filters are `dateFilters.ts`, which send inclusive bare days for the server to read in the same preference.
  - **CLI**: days are read on the machine's calendar (`localDay`), the way `git log` and `date` read them, and `LocalZoneName()` goes out beside every date bound on a timestamp column.
  - **Scheduler**: the admin's preference, described in `docs/scheduler.md`.
- **A wall clock is resolved before it is compared, and printed without resolving.** The reading is what goes on the page, with the zone named beside it — converting it into the reader's zone moves the number and says nothing about where the event is. Sorting, "has it happened", and "how long until" all need the instant, so they resolve first. Comparing the readings puts a 09:00 in Tokyo after an 08:00 in New York, thirteen hours backwards.
- **A day never travels as a `datetime`.** The Vue side holds a day as a `YYYY-MM-DD` key. A value with no offset is a reading, which `formatDate` and `dayKeyOf` print as written; one carrying an offset is an instant, and moves into the display zone. If a day-shaped value comes back with a `Z`, the column is the wrong type.
- **The Go CLI decodes a day as a `string`, never a `time.Time`.** `time.Time`'s JSON decode requires RFC3339 and rejects a bare day, and `client.go` decodes a whole slice in one call — so one dated row fails the entire command. `api.Countdown.DueDate` is the shape to copy.
- **Docker Compose overrides**: List fields (`ports`, `volumes`, `environment`) **merge by default** across compose files. When a test/dev compose redefines a list that exists in the base compose, use `!override` to replace instead of append (e.g., `ports: !override`). Without this, both port mappings apply and cause "port already allocated" errors.

### Styling & Design Cohesion

**Global over scoped**: visual styling comes from the shared SCSS in `frontend/src/assets/sass/`; a scoped `<style>` block handles layout only (flexbox, grid, spacing).

**Neumorphic shadow variables** (`layout/_grid.scss`): `--floating-box` is raised, `--floating-box-pressed` is sunken, and `--bubble-box` / `--bubble-box-pressed` are the hover states.

**Shared mixins** (`components/`): `data-table`, `card-row` and `list-item` define the full visual pattern; a consumer includes one at entity level and sets only `grid-template-columns`. `double-bevel-button` takes `$button-size` and derives every other proportion, so never override proportions per caller.

**Empty states**: every `{block}__empty` is exactly `color: var(--clr-gray-500); font-style: italic`, with layout inherited from its container.

**Design-style-switch readiness** (⚠️ MANDATORY): The site is being built toward a future design style switcher (neumorphic / jagged / bubbly / etc.) that changes shape, shadow, and border properties site-wide — the same way the color theme switcher changes all colors today. To keep this feasible:

- **NEVER** hardcode `box-shadow`, `border-radius`, or button shapes in scoped `<style>` blocks. Always reference the CSS variable (`--floating-box`, `--border-radius`, etc.).
- **NEVER** hardcode chart colors, grid colors, or text colors in Chart.js config. Use `getThemeColors()` / `paletteColors()` from `useStatsCharts` composable, which reads live CSS custom properties.
- All visual effects must flow through CSS variables defined in the SCSS abstracts layer. Scoped styles handle **layout only** (flexbox, grid, gaps, padding).
- When the switcher is built, it will toggle a `data-design` attribute on `<html>` and swap variable sets. Components that follow these rules will just work.

**Stats pages** use the shared kit in `frontend/src/components/stats/` and `frontend/src/composables/useStatsCharts.ts`, whose chart colors derive from the active theme's CSS custom properties.

### Component Architecture — Consistency Over Convenience

**Every reusable pattern gets a wrapper per entity**: every entity using `AddEditModal` gets its own wrapper (`AddEditTaskModal`, `AddEditCountdownModal`) holding its form markup, state and validation, whatever the form's size.
Either every page follows a pattern or none does; there is no rule-of-thumb threshold for components, composables or shared SCSS.

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
9. **A read answering with a list takes `RowLimit` and `apply_row_limit`** from
   `ichrisbirch/services/row_limit.py` — `CappedRowLimit` where the subject grows
   without end and a number is the right default. Declaring `limit: int | None`
   by hand loses the floor, so a negative reaches SQL as `LIMIT -1`, and a falsy
   test answers `limit=0` with the whole collection. Both are invisible in the
   response. `test_every_read_that_takes_a_limit_declares_the_shared_one` walks
   the routes and fails on either, and adding the endpoint to `LIMITED_READS` in
   the same file is what gets it the five behavioral cases.

### Adding a Vue Page

A page is a Pinia store (`createLogger`, `ApiError`, `error: ref<ApiError | null>`), a `<script setup>` view that fetches in `onMounted` and reports through `useNotifications()`, a lazy-loaded route in `frontend/src/router.ts`, and an entry in `AppSidebar.vue`.
Add its path to `deploy-containers/traefik/vue-paths.txt` and run `icbops routing generate`.
Unit tests mock the API with `vi.mock`; E2E runs through `app.docker.localhost`, never `vue.docker.localhost`, so CORS faults surface.

### Logging

Python logs through structlog into the stdlib root logger, to stderr plus a file when `LOG_FILE` is set; `LOG_FORMAT` (`console`/`json`), `LOG_LEVEL` and `LOG_COLORS` configure it.
Requests are traced by `X-Request-ID`.
Vue logs through consola via `createLogger('ModuleName')`, in structlog's key=value shape, and as JSON for Loki in production.
`./ops/icbops {dev,testing} logs [service]` reads a running environment's logs.
