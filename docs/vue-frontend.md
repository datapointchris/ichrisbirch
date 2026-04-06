# Vue 3 Frontend

The ichrisbirch frontend is a Vue 3 SPA with TypeScript, served behind `app.docker.localhost` via Traefik path-based routing.

## Architecture

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | Vue 3.5+ | Component-based SPA |
| Language | TypeScript (strict mode) | Type safety |
| State | Pinia | Reactive store per feature |
| Routing | Vue Router | Client-side routing with lazy-loaded views |
| Build | Vite 7.x | Fast HMR in dev, optimized production builds |
| Styling | SCSS (ITCSS) | Global SCSS system in `frontend/src/assets/sass/` |
| HTTP | Axios | API calls with request tracing |
| Logging | consola | Structured logging matching structlog format |
| Unit Tests | Vitest + Vue Test Utils | Store and component testing |
| E2E Tests | Playwright | Full-stack testing through Traefik |

## Key Infrastructure Files

| File | Purpose |
|------|---------|
| `frontend/src/utils/logger.ts` | consola-based structured logger (createLogger pattern) |
| `frontend/src/api/errors.ts` | ApiError class with status, detail, validationErrors, requestId |
| `frontend/src/api/client.ts` | Axios with X-Request-ID tracing, structured logging, WeakMap metadata |
| `frontend/src/stores/countdowns.ts` | Reference implementation for Pinia store with error handling |
| `frontend/e2e/countdowns.spec.ts` | Reference E2E tests through real Traefik routing |

## Development

### Running the Vue Frontend

The Vue service starts automatically with `./cli/icb dev start`. It runs as a Vite dev server on port 5173, proxied through Traefik at `app.docker.localhost`.

### Auth in Development

Traefik's `dev-authelia-sim` middleware injects `Remote-User` and `Remote-Email` headers on API requests, simulating what Authelia does in production. No login page or token management needed in dev.

### Auth in Production

Authelia ForwardAuth protects all app routes. The API bypasses ForwardAuth (uses PATs/JWTs for MCP and programmatic access).

## Testing

Three-layer strategy that catches TypeScript errors, logic bugs, and integration issues:

### Build Verification

```bash
npm run test:build   # vue-tsc + vite build
```

Catches: TypeScript errors, missing imports, dependencies missing in Docker.

### Unit Tests

```bash
npm run test:unit    # Vitest (681 tests)
npm run test:watch   # Watch mode
npm run test:ui      # Interactive UI
```

Catches: Store logic errors, error handling paths, API response parsing.

### E2E Tests

```bash
npm run test:e2e     # Playwright (85 tests, requires test containers)
npm run test:e2e:ui  # Interactive UI
```

Catches: CORS failures, auth header issues, Traefik routing, real CRUD operations.

E2E tests run through `app.docker.localhost` (not `vue.docker.localhost`) to test the real user path including cross-origin API calls to `api.docker.localhost`.

### All Tests

```bash
npm test             # Build check + unit tests
```

## Adding a New Page

1. Create Pinia store in `frontend/src/stores/` using `createLogger` and `ApiError`
2. Create Vue view in `frontend/src/views/`
3. Add route in `frontend/src/router.ts`
4. Add sidebar link in `frontend/src/components/AppSidebar.vue`
5. Add path to `deploy-containers/traefik/vue-paths.txt` and run `ich routing generate`
6. Write unit tests in `frontend/src/stores/__tests__/`
7. Write E2E tests in `frontend/e2e/`
8. Run `npm test` and `npm run test:e2e` before considering the page done

## Pre-commit Hooks

Three hooks gate Vue code quality on every commit:

- **vue-eslint**: ESLint with auto-fix (`npm run lint:fix`)
- **vue-prettier**: Prettier formatting (`npm run format`)
- **vue-typecheck**: TypeScript checking (`npm run typecheck`)

Only triggered by changes to `frontend/**/*.{vue,ts,tsx,js,jsx}` files.

## Bugs and Gotchas

Lessons learned during infrastructure setup:

- **Docker Alpine IPv6**: `wget` resolves `localhost` to `::1` but Node binds IPv4 only. Use `127.0.0.1` in health checks.
- **CORS with credentials**: `Access-Control-Allow-Headers: *` is NOT a wildcard when `credentials: true` (per spec). Must list headers explicitly.
- **consola log levels**: Inverted from Python (error=0, debug=4). The `levelName()` function in `logger.ts` handles this.
- **Named volumes vs host node_modules**: `npm install` on the host doesn't affect the container's named volume. Use `docker exec npm install` or add a `test:build` step.
