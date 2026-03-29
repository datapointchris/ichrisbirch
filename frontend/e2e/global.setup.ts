import { test, expect } from '@playwright/test'

const isDevEnv = process.env.E2E_ENV === 'dev'
const appURL = isDevEnv ? 'https://app.docker.localhost' : 'https://app.test.localhost:8443'

// Gate for all E2E tests — if the API, database, or frontend is unreachable,
// skip the entire test suite instead of waiting for every test to timeout.
// Pattern matches Python's DockerComposeTestEnvironment.verify_test_services().

test('API is reachable', async ({ request }) => {
  test.setTimeout(180_000)
  await expect(async () => {
    const response = await request.get('/users/me/', {
      headers: { 'Remote-User': 'user@icb.com' },
    })
    expect(response.ok()).toBeTruthy()
  }).toPass({ intervals: [5_000] })
})

test('frontend is serving', async ({ request }) => {
  test.setTimeout(300_000)
  await expect(async () => {
    const response = await request.get(appURL, { ignoreHTTPSErrors: true })
    expect(response.ok()).toBeTruthy()
  }).toPass({ intervals: [5_000] })
})
