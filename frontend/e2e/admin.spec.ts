import { test, expect } from '@playwright/test'

// Smoke tests only — rendering details (sections, DB stats, masked secrets,
// status classes, user toggles) are covered by component integration tests
// in src/views/__tests__/AdminViews.test.ts

// E2E tests run as user@icb.com for most routes, but admin API routes
// (/admin/*) use test-authelia-sim-admin which injects admin@icb.com,
// so admin data endpoints return data instead of 403.

test.describe('Admin Pages', () => {
  test('API calls succeed through Traefik routing (CORS check)', async ({ page }) => {
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/admin')
    await expect(page.locator('.admin-section').first()).toBeVisible({ timeout: 10000 })
    expect(apiErrors).toEqual([])
  })

  test('loads system health page with sections', async ({ page }) => {
    await page.goto('/admin')
    await expect(page).toHaveTitle('Admin — System | iChrisBirch')
    await expect(page.locator('.admin-section').first()).toBeVisible({ timeout: 10000 })
  })

  test('navigates between all tabs', async ({ page }) => {
    await page.goto('/admin')
    await expect(page.locator('.admin-subnav__link--active', { hasText: 'System Health' })).toBeVisible()

    await page.locator('.admin-subnav__link', { hasText: 'Scheduler' }).click()
    await expect(page).toHaveTitle('Admin — Scheduler | iChrisBirch')

    await page.locator('.admin-subnav__link', { hasText: 'Users' }).click()
    await expect(page).toHaveTitle('Admin — Users | iChrisBirch')

    await page.locator('.admin-subnav__link', { hasText: 'Config' }).click()
    await expect(page).toHaveTitle('Admin — Config | iChrisBirch')
  })

  test('sidebar shows active state on admin pages', async ({ page }) => {
    await page.goto('/admin')
    await expect(page.locator('.nav-link--active', { hasText: 'Admin' })).toBeVisible()
  })
})
