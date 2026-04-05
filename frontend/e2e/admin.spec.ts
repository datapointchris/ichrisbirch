import { test, expect } from '@playwright/test'

// Smoke tests only — rendering details (sections, DB stats, masked secrets,
// status classes, user toggles) are covered by component integration tests
// in src/views/__tests__/AdminViews.test.ts

// E2E tests run as admin@icb.com (test-authelia-sim injects admin headers),
// matching the dev environment. The Vue router guard checks auth.isAdmin
// before allowing access to /admin routes.

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
    await expect(page.getByTestId('admin-subnav-system')).toHaveClass(/subnav__link--active/)

    await page.getByTestId('admin-subnav-scheduler').click()
    await expect(page).toHaveTitle('Admin — Scheduler | iChrisBirch')

    await page.getByTestId('admin-subnav-users').click()
    await expect(page).toHaveTitle('Admin — Users | iChrisBirch')

    await page.getByTestId('admin-subnav-config').click()
    await expect(page).toHaveTitle('Admin — Config | iChrisBirch')
  })

  test('sidebar shows active state on admin pages', async ({ page }) => {
    await page.goto('/admin')
    await expect(page.locator('.nav-link--active', { hasText: 'Admin' })).toBeVisible()
  })
})
