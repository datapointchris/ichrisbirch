import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright E2E tests for ichrisbirch Vue frontend.
 *
 * Tests run against the real frontend + API + database (Docker-based).
 * Sequential execution to maintain consistent database state.
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: 'list',
  timeout: 30000,

  use: {
    baseURL: 'https://vue.docker.localhost',
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
