# Adding A New Application

For this document example we will be creating a new app called `Items`

|                                      |           |
| ------------------------------------ | --------- |
| :material-database: db table         | `items`   |
| :simple-sqlalchemy: sqlalchemy model | `Item`    |
| :simple-pydantic: pydantic schema    | `Item`    |
| :material-api: api endpoint          | `/items/` |
| :material-application: frontend      | `/items`  |

## Backend (Required for All Features)

### 1. SQLAlchemy Model

:material-import: Import new models into `ichrisbirch/alembic/env.py`
:material-import: Import new models into `ichrisbirch/models/__init__.py`

```python
from ichrisbirch import models

item = models.Item(**data)
```

### 2. Pydantic Schema

:material-import: Import new schemas into `ichrisbirch/schemas/__init__.py`

```python
from ichrisbirch import schemas

item = schemas.ItemCreate(**data)
```

### 3. API Router and Endpoints

Create endpoint file in `ichrisbirch/api/endpoints/items.py`, register in `ichrisbirch/api/main.py`.

### 4. Database Migration

```bash
alembic revision --autogenerate -m "add items table"
alembic upgrade head
```

### 5. Test Data

:material-test: Add testing data into `tests/test_data/`
:material-import: Import in `tests/test_data/__init__.py`

### 6. API Tests

Create `tests/ichrisbirch/api/endpoints/test_items.py` using `ApiCrudTester` or direct assertions.

## Vue Frontend (Migrated Pages)

For new pages being built in Vue (the standard going forward):

### 1. Pinia Store (`frontend/src/stores/items.ts`)

- TypeScript interfaces matching Pydantic schemas
- Use `createLogger('ItemsStore')` for structured logging
- Use `ApiError` / `extractApiError` for error handling
- Expose reactive `error` ref as `ApiError | null`

### 2. Vue View (`frontend/src/views/ItemsView.vue`)

- Use the store for data and actions
- Display errors via `ApiError.userMessage`
- Add route in `frontend/src/router.ts`

### 3. Navigation Link

Add link in `frontend/src/components/AppSidebar.vue`

### 4. Traefik Routing

Update `docker-compose.dev.yml` to add the path to the Vue router rule (priority 100):

```yaml
- "traefik.http.routers.vue.rule=Host(`app.docker.localhost`) && (PathPrefix(`/countdowns`) || PathPrefix(`/items`))"
```

### 5. Tests

- **Unit tests**: `frontend/src/stores/__tests__/items.test.ts` — mock API, test CRUD + error paths
- **E2E tests**: `frontend/e2e/items.spec.ts` — Playwright through `app.docker.localhost`

### 6. Verify

```bash
cd frontend
npm test           # Build check + 55 unit tests
npm run test:e2e   # E2E through Traefik (requires dev containers)
```

## Flask Frontend (Legacy, Unmigrated Pages Only)

For pages not yet migrated to Vue:

### 1. Flask Blueprint (`ichrisbirch/app/routes/items.py`)

Register in `ichrisbirch/app/main.py`.

### 2. Jinja2 Templates (`ichrisbirch/app/templates/items/`)

Extend base template, use WTForms for forms.

### 3. Flask Navigation Link

Add link in `ichrisbirch/app/templates/base.html`.

### 4. App Route Tests

Create `tests/ichrisbirch/app/routes/test_items.py`.
