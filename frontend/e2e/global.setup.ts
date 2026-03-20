import { test, expect } from '@playwright/test'

// Gate for all E2E tests — if the API or database is unreachable,
// skip the entire test suite instead of waiting for every test to timeout.
test('test environment is reachable', async ({ request }) => {
  const response = await request.get('/users/me/', {
    headers: { 'Remote-User': 'user@icb.com' },
  })
  expect(response.ok()).toBeTruthy()
})
