# Vue 3 Frontend

The ichrisbirch frontend is a Vue 3 SPA with TypeScript, served behind `app.docker.localhost` via Traefik path-based routing.

## Architecture

| Component | Technology | Purpose |
| --- | --- | --- |
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
| --- | --- |
| `frontend/src/utils/logger.ts` | consola-based structured logger (createLogger pattern) |
| `frontend/src/api/errors.ts` | ApiError class with status, detail, validationErrors, requestId |
| `frontend/src/api/client.ts` | Axios with X-Request-ID tracing, structured logging, WeakMap metadata |
| `frontend/src/stores/countdowns.ts` | Reference implementation for Pinia store with error handling |
| `frontend/e2e/countdowns.spec.ts` | Reference E2E tests through real Traefik routing |

## Development

### Running the Vue Frontend

The Vue service starts automatically with `./ops/icbops dev start`. It runs as a Vite dev server on port 5173, proxied through Traefik at `app.docker.localhost`.

### Auth in Development

Traefik's `dev-authelia-sim` middleware injects `Remote-User` and `Remote-Email` headers on API requests, simulating what Authelia does in production. No login page or token management needed in dev.

### Auth in Production

Authelia ForwardAuth protects all app routes. The `icb` CLI targets the same `ichrisbirch.com/api` with an Authelia bearer token, which the edge carries past ForwardAuth.

## Testing

Three-layer strategy that catches TypeScript errors, logic bugs, and integration issues:

### Build Verification

```bash
npm run test:build   # vue-tsc + vite build
```

Catches: TypeScript errors, missing imports, dependencies missing in Docker.

### Unit Tests

```bash
npm run test:unit    # Vitest
npm run test:watch   # Watch mode
npm run test:ui      # Interactive UI
```

Catches: Store logic errors, error handling paths, API response parsing.

### E2E Tests

```bash
npm run test:e2e     # Playwright, requires test containers
npm run test:e2e:ui  # Interactive UI
```

Catches: CORS failures, auth header issues, Traefik routing, real CRUD operations.

E2E tests run through `app.docker.localhost` (not `vue.docker.localhost`) to test the real user path including cross-origin API calls to `api.docker.localhost`.

The `phone` Playwright project reruns the specs its `testMatch` names on a Pixel 7 profile, at phone size and with touch. A page meant to be used from a phone adds its spec there.

### All Tests

```bash
npm test             # Build check + unit tests
```

## Adding a New Page

1. Create Pinia store in `frontend/src/stores/` using `createLogger` and `ApiError`
2. Create Vue view in `frontend/src/views/`
3. Add route in `frontend/src/router.ts`
4. Add sidebar link in `frontend/src/components/sidebarLinks.ts`, to `allMainLinks` and `DEFAULT_SIDEBAR_ORDER`
5. Add path to `deploy-containers/traefik/vue-paths.txt` and run `icbops routing generate`
6. Write unit tests in `frontend/src/stores/__tests__/`
7. Write E2E tests in `frontend/e2e/`
8. Run `npm test` and `npm run test:e2e` before considering the page done

## Phone Layout

One width separates a phone from everything else. `abstracts/_breakpoints.scss` holds it as `$phone-max-width` and wraps it in `@include breakpoints.phone`. `base/_base.scss` publishes the same value as the `--phone-max-width` CSS variable, and `usePhoneViewport()` reads that variable. So a stylesheet and a script switch at the same width, and changing the width is one edit.

Under that width the sidebar is off-canvas. It starts closed, closes on every navigation, and closes when its backdrop is tapped. It opens from the menu button in the phone bar, a sticky strip `App.vue` puts above every page. The button lives in that bar because a floating one sits over whatever scrolls beneath it, such as a list's check-off column.

A page's own sticky header sets `top: var(--page-sticky-top)`. On a phone that value clears the phone bar, and elsewhere it clears only the notch.

The page reaches the screen edges, padded by the `env(safe-area-inset-*)` insets, because `index.html` sets `viewport-fit=cover` and a translucent status bar for the home-screen app. `public/manifest.webmanifest` and `public/icons/` make the site installable to a home screen. The manifest link carries `crossorigin="use-credentials"`. Without it the browser fetches the manifest with no cookies, and production answers a request with no session by redirecting to the login page.

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
