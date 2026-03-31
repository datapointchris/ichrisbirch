# Testing Infrastructure Overview

This document provides a comprehensive overview of the testing infrastructure in the ichrisbirch project. The testing infrastructure supports the FastAPI backend API and Vue 3 SPA frontend.

## Table of Contents

1. [Testing Architecture](#testing-architecture)
2. [Test Environment Setup](#test-environment-setup)
3. [Test Data Management](#test-data-management)
4. [Test Clients](#test-clients)
5. [Fixtures](#fixtures)
6. [Writing Tests](#writing-tests)
7. [Vue Frontend Testing](#vue-frontend-testing)
8. [Related Documentation](#related-documentation)

## Testing Architecture

The testing infrastructure follows a layered approach:

![Testing Architecture Overview](../images/generated/testing_overview.svg)

The architecture ensures that:

1. Tests run in a controlled, isolated environment
2. The API server is available for testing
3. Test data is managed consistently
4. Authentication and authorization can be tested effectively

## Test Environment Setup

The test environment uses a separate Docker Compose environment with isolated database and Redis, running alongside dev on alternate ports. Test containers are ephemeral — the postgres data volume is destroyed on `testing stop`.

## Test Data Management

Test data is managed through seed modules (`ichrisbirch/seeders/`) and test fixtures. The seed system uses per-entity seeders that populate the test database on container startup.

## Test Clients

Test clients provide interfaces to interact with the API server:

1. **API Test Client**: Based on FastAPI's TestClient
2. **Authenticated clients**: Module-scoped fixtures for logged-in and admin access

## Fixtures

The testing infrastructure provides fixtures at different scopes:

1. **Session-scoped**: Docker orchestration, table lifecycle, test users
2. **Module-scoped**: `test_api`, `test_api_logged_in`, `test_api_logged_in_admin`
3. **Function-scoped**: `*_function` suffix variants for test isolation

See the [fixtures documentation](fixtures.md) for more details.

## Writing Tests

See the [writing tests guide](writing_tests.md) for information on how to write effective tests using this infrastructure.

## Vue Frontend Testing

The Vue frontend uses a four-layer testing strategy:

| Layer | Tool | Tests | Duration | What it catches |
|-------|------|-------|----------|-----------------|
| Build | `vue-tsc` + `vite build` | — | ~10s | TypeScript errors, missing imports |
| Store/Unit | Vitest | ~347 | ~5s | Store logic, composables, utilities |
| Component | Vitest + `@pinia/testing` | ~225 | ~2s | View rendering, store wiring, modals |
| E2E | Playwright | ~80 | ~50s | CORS, Traefik routing, real CRUD |

### Build Verification (`npm run test:build`)

Runs `vue-tsc` (TypeScript checking) and `vite build` to catch:

- TypeScript errors and missing type declarations
- Missing imports and broken module resolution
- Dependencies installed on host but missing in Docker container

### Store/Unit Tests (`npm run test:unit`)

Vitest with Vue Test Utils. Tests Pinia stores, composables, and utility functions with mocked API calls.

- Located in `frontend/src/**/__tests__/` (store and composable directories)
- API mocked via `vi.mock('@/api/client')`

### Component Integration Tests (part of `npm run test:unit`)

Vitest with `@pinia/testing`. Mounts real Vue view components with controlled store state.

- Located in `frontend/src/views/__tests__/`
- Pattern: `createTestingPinia({ initialState, stubActions: true, createSpy: vi.fn })`
- Stub child components (modals, subnavs) and mock composables (`useNotifications`, `formatDate`)
- Verify: rendering states, conditional CSS classes, store action calls on user interaction, modal prop wiring
- Every view page has a corresponding test file (14 files total)

### E2E Tests (`npm run test:e2e`)

Playwright tests running through real Traefik routing at `https://app.docker.localhost`. Trimmed to smoke-only — each page keeps:

- CORS/API reachability check
- Page load with correct title
- Sidebar nav active state
- One CRUD roundtrip (create + delete)

Interaction-heavy tests (edit modals, toggles, filters, search, sort) live in component tests. Every E2E file has a comment pointing to its component test counterpart.

- Located in `frontend/e2e/`
- Requires test containers running (`./cli/icb testing start`)
- Sequential execution (`workers: 1`) to maintain consistent database state

### Running Vue Tests

```bash
cd frontend

# Build check + all unit/component tests (fast, no containers needed)
npm test

# E2E tests (requires test containers)
npm run test:e2e

# E2E with interactive UI
npm run test:e2e:ui
```

### Pre-commit Integration

Five pre-commit hooks gate Vue code quality on every commit:

- **vue-eslint**: Linting with auto-fix
- **vue-prettier**: Code formatting
- **vue-typecheck**: TypeScript type checking
- **vue-test**: Vitest unit + component tests
- **vue-e2e**: Playwright E2E smoke tests

## Related Documentation

- [Test Fixtures](fixtures.md)
- [Test Data Management](test_data.md)
- [Test Environment Configuration](environment.md)
- [Writing Tests](writing_tests.md)
