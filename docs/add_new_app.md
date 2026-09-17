# Adding A New Application

For this document example we will be creating a new app called `Widgets`

| Layer | Name |
| --- | --- |
| :material-database: db table | `widgets` |
| :simple-sqlalchemy: sqlalchemy model | `Widget` |
| :simple-pydantic: pydantic schema | `Widget` |
| :material-api: api endpoint | `/widgets/` |
| :material-application: frontend | `/widgets` |

## Backend (Required for All Features)

### 1. SQLAlchemy Model

:material-import: Import new models into `ichrisbirch/alembic/env.py`
:material-import: Import new models into `ichrisbirch/models/__init__.py`

```python
from ichrisbirch import models

widget = models.Widget(**data)
```

### 2. Pydantic Schema

:material-import: Import new schemas into `ichrisbirch/schemas/__init__.py`

```python
from ichrisbirch import schemas

widget = schemas.WidgetCreate(**data)
```

### 3. API Router and Endpoints

Create endpoint file in `ichrisbirch/api/endpoints/widgets.py`, register in `ichrisbirch/api/main.py`.

### 4. Database Migration

```bash
alembic revision --autogenerate -m "add widgets table"
alembic upgrade head
```

### 5. Seeder (Required)

:material-seed: Create `scripts/seed/seeders/widgets.py` implementing `seed(session, scale)` and `clear(session)`
:material-import: Register in `scripts/seed/seeders/__init__.py` — add to the imports and to `SEED_ORDER` after any FK dependencies

If the model uses lookup tables (FK to a `*_TEXT PRIMARY KEY` table), also add the lookup values to `LOOKUP_DATA` in `ichrisbirch/database/initialization.py` — that dict is re-seeded after every test truncate, separate from the Alembic migration seed.

### 6. Test Data

:material-test: Add testing data into `tests/test_data/`
:material-import: Import in `tests/test_data/__init__.py`

### 7. API Tests

Create `tests/ichrisbirch/api/endpoints/test_widgets.py` using `ApiCrudTester` or direct assertions.

`ApiCrudTester` defaults `expected_length=3`, so the test data holds exactly
three rows unless you pass a different count.

### 8. Row limit on every list read

A read answering with a list takes `RowLimit` and `apply_row_limit` from
`ichrisbirch/services/row_limit.py`, applied last so the cap takes the top of
what the filters left. Declaring `limit: int | None` by hand loses the floor, so
a negative reaches SQL as `LIMIT -1`, and a falsy test answers `limit=0` with
the whole collection — both invisible in the response.

`test_every_read_that_takes_a_limit_declares_the_shared_one` walks the live
routes and fails on either. Add the endpoint to `LIMITED_READS` in the same file
to get the five behavioral cases covering what zero means.

## Vue Frontend (Migrated Pages)

For new pages being built in Vue (the standard going forward):

### 1. Pinia Store (`frontend/src/stores/widgets.ts`)

- TypeScript interfaces matching Pydantic schemas
- Use `createLogger('WidgetsStore')` for structured logging
- Use `ApiError` / `extractApiError` for error handling
- Expose reactive `error` ref as `ApiError | null`

### 2. Vue View (`frontend/src/views/WidgetsView.vue`)

- Use the store for data and actions
- Display errors via `ApiError.userMessage`
- Add route in `frontend/src/router.ts`

### 3. Navigation Link

Add link in `frontend/src/components/AppSidebar.vue`

### 4. Traefik Routing

Add the new path to `deploy-containers/traefik/vue-paths.txt` and regenerate routing:

```bash
echo "/widgets" >> deploy-containers/traefik/vue-paths.txt
./ops/icbops routing generate
```

### 5. Tests

- **Unit tests**: `frontend/src/stores/__tests__/widgets.test.ts` — mock API, test CRUD + error paths
- **E2E tests**: `frontend/e2e/widgets.spec.ts` — Playwright through `app.docker.localhost`

### 6. Verify

```bash
cd frontend
npm test           # Build check + unit tests
npm run test:e2e   # E2E through Traefik (requires dev containers)
```

## `icb` CLI

The Go resource CLI in `cli/` is the programmatic front door to the same API, so
a new endpoint group reaches it too. A resource adds two files and two test
files; everything else is shared plumbing.

### 1. Wire contract (`cli/internal/api/widgets.go`)

- `Widget`, `WidgetCreateInput`, `WidgetUpdateInput`, and a `WidgetFilter` with a
  `query()` where the list read narrows.
- Nullable columns are pointers. Optional create fields and every update field
  carry `,omitempty`, so an unset flag is omitted rather than sent as `null`.
- A calendar day is a `string`, never a `time.Time` — Go's decode requires
  RFC3339 and rejects a bare day, and the client decodes a whole slice in one
  call, so one dated row would fail the entire command.
- Client methods go through `c.get` / `c.send`; a resource file never touches
  `http.NewRequest`. `applyLimit(params, limit)` from `row_limit.go` puts the
  cap on.

### 2. Commands (`cli/internal/cli/widgets.go`)

`newWidgetsCommand()` with `list`, `show`, `search`, `create`, `edit`, `delete`.
The verbs are `show` and `edit`, not `get` and `update`.

- `withNotFoundHints(cmd, ...)` — a tree walk fails without it.
- `addLimitFlag(cmd, &limit)` rather than registering `--limit` by hand.
- `--json` on every read, short-circuiting to `encodeJSON`.
- `create` and `edit` share one flag struct and one `addWidgetFlags` function.
- `delete` fetches first, so the confirmation names the row.

A resource with a closed vocabulary follows `[]prompt.Field` for its guided
create. Both ways of supplying the choices are in the tree and they answer
different questions, so pick deliberately rather than by whichever file you
opened.

**Declared** — `tasks.go` holds `api.TaskCategories` as a `[]string`. Usage
errors never depend on the network, the values appear in `--help`, and a display
label can be spelled beside each one. The cost is that the list is copied per
client: `task_categories` is a lookup table whose values also sit in Python, in
TypeScript and in Go, and nothing keeps the three level.

**Fetched** — `strains.go` reads them from the API on create and edit, and
`items.go` reads a project list the same way. Adding a value stays an insert on
the server. Three things come with it:

- The fetch has to run after every refusal that needs no server state, or a
  usage error becomes exit 1 whenever the API is unreachable.
- Display labels stay compiled into each client, because a lookup table carries
  a name and no label column.
- A value added in production still needs a migration, so that the insert is
  replayed wherever the database is rebuilt from zero.

Fetch where the vocabulary is an open set that grows. Declare where it is a
closed lifecycle each client has to render differently — `strains` does both,
and `ichrisbirch/models/strain.py` says which is which and why.

### 3. Register

`newWidgetsCommand()` in `NewRootCommand` (`cli/internal/cli/root.go`), keeping
`applyUsageTemplate(root)` last. Add `{"widgets", "list"}` to the roster in
`cli/internal/cli/limit_test.go`. Update the resource lists in `cli/README.md`
and in `root.go`'s own `Long`.

### 4. Tests and verify

`cli/internal/api/widgets_test.go` drives an `httptest` server and asserts the
captured query string and request body. `cli/internal/cli/widgets_test.go` runs
the real command tree through `runTree` and asserts exit codes.

```bash
task cli:lint && task cli:test
ICB_API_BASE=https://api.docker.localhost icb widgets list
```

The installed `icb` always targets production regardless of working directory,
which is why a check against dev sets `ICB_API_BASE`.
