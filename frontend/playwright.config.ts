import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright E2E tests for ichrisbirch Vue frontend.
 *
 * Tests run against the real frontend + API + database (Docker-based).
 * Sequential execution to maintain consistent database state.
 *
 * By default, tests run inside this checkout's test stack, in its vue
 * container, which `./ops/icbops test e2e` starts them in. The stack publishes
 * no ports. Set E2E_ENV=dev to run on the host against dev containers
 * (app.docker.localhost).
 */

const isDevEnv = process.env.E2E_ENV === 'dev'
if (!isDevEnv && !process.env.ICB_TEST_STACK) {
  throw new Error('The test stack publishes no ports, so its e2e suite runs inside it: ./ops/icbops test e2e')
}
const baseURL = isDevEnv ? 'https://app.docker.localhost' : 'https://app.test.localhost:8443'
const apiURL = isDevEnv ? 'https://api.docker.localhost' : 'https://api.test.localhost:8443'
// Chromium resolves every *.localhost name to loopback without asking DNS, so
// inside the stack it is told that the test hosts are Traefik's container.
const launchOptions = isDevEnv ? {} : { args: ['--host-resolver-rules=MAP *.test.localhost traefik'] }

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [['list'], ['json', { outputFile: '../.test-reports/playwright-report.json' }]],
  timeout: 20000,
  maxFailures: 3,

  use: {
    // Must use app.*.localhost (not vue.*.localhost) to test through
    // Traefik path-based routing — this is what users actually hit, and it's
    // the only way to catch cross-origin CORS issues with api.*.localhost.
    baseURL,
    launchOptions,
    ignoreHTTPSErrors: true,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'setup',
      testMatch: /global\.setup\.ts/,
      retries: 0,
      use: { baseURL: apiURL },
    },
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
      dependencies: ['setup'],
    },
    {
      // Pixel 7 runs on Chromium, so phone size and touch need no second browser.
      name: 'phone',
      use: { ...devices['Pixel 7'] },
      testMatch: /(shell|shopping|today)\.spec\.ts/,
      dependencies: ['setup'],
    },
  ],
})
