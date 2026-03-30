import { test, expect } from '@playwright/test'

// Smoke tests only — link rendering, admin links, and target=_blank checks
// are covered by component integration tests in
// src/views/__tests__/HomeView.test.ts

test.describe('Home Page', () => {
  test('loads the page and displays heading', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveTitle('Home | iChrisBirch')
    await expect(page.locator('h1', { hasText: 'Chris Birch' })).toBeVisible()
    await expect(page.locator('h2', { hasText: 'Data Engineer' })).toBeVisible()
  })
})
