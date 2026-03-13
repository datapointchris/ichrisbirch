import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright E2E tests for ichrisbirch Vue frontend.
 *
 * Tests run against the real frontend + API + database (Docker-based).
 * Sequential execution to maintain consistent database state.
 *
 * By default, tests run against test containers (app.test.localhost:8443).
 * Set E2E_ENV=dev to run against dev containers (app.docker.localhost).
 */

const isDevEnv = process.env.E2E_ENV === 'dev'
const baseURL = isDevEnv ? 'https://app.docker.localhost' : 'https://app.test.localhost:8443'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: 'list',
  timeout: 30000,

  use: {
    // Must use app.*.localhost (not vue.*.localhost) to test through
    // Traefik path-based routing — this is what users actually hit, and it's
    // the only way to catch cross-origin CORS issues with api.*.localhost.
    baseURL,
    ignoreHTTPSErrors: true,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
