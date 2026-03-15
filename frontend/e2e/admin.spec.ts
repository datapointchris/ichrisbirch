import { test, expect } from '@playwright/test'

// E2E tests run as user@icb.com for most routes, but admin API routes
// (/admin/*) use test-authelia-sim-admin which injects admin@icb.com,
// so admin data endpoints return data instead of 403.

test.describe('Admin System Health Page', () => {
  test('loads and displays system health data', async ({ page }) => {
    await page.goto('/admin')
    await expect(page).toHaveTitle('Admin — System | iChrisBirch')
    await expect(page.locator('h1', { hasText: 'Admin' })).toBeVisible()
    // Wait for system health data to load
    await expect(page.locator('.admin-section').first()).toBeVisible({ timeout: 10000 })
    await expect(page.locator('h2', { hasText: 'Server' })).toBeVisible()
    await expect(page.locator('h2', { hasText: 'Database' })).toBeVisible()
    await expect(page.locator('h2', { hasText: 'Redis' })).toBeVisible()
    await expect(page.locator('h2', { hasText: 'Disk' })).toBeVisible()
    await expect(page.locator('h2', { hasText: 'Recent Errors' })).toBeVisible()
  })

  test('displays database stats with expandable table row counts', async ({ page }) => {
    await page.goto('/admin')
    await expect(page.locator('h2', { hasText: 'Database' })).toBeVisible({ timeout: 10000 })
    await expect(page.getByText(/\d+\.\d+ MB/)).toBeVisible()
    await expect(page.locator('summary', { hasText: 'Table Row Counts' })).toBeVisible()
  })

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
})

test.describe('Admin Sub-navigation', () => {
  test('subnav links are visible', async ({ page }) => {
    await page.goto('/admin')
    await expect(page.locator('.admin-subnav__link', { hasText: 'System Health' })).toBeVisible()
    await expect(page.locator('.admin-subnav__link', { hasText: 'Scheduler' })).toBeVisible()
    await expect(page.locator('.admin-subnav__link', { hasText: 'Users' })).toBeVisible()
    await expect(page.locator('.admin-subnav__link', { hasText: 'Config' })).toBeVisible()
    await expect(page.locator('.admin-subnav__link', { hasText: 'AutoTasks' })).toBeVisible()
  })

  test('system health tab is active by default', async ({ page }) => {
    await page.goto('/admin')
    await expect(page.locator('.admin-subnav__link--active', { hasText: 'System Health' })).toBeVisible()
  })

  test('navigates between all tabs', async ({ page }) => {
    await page.goto('/admin')
    await expect(page.locator('.admin-subnav__link--active', { hasText: 'System Health' })).toBeVisible()

    await page.locator('.admin-subnav__link', { hasText: 'Scheduler' }).click()
    await expect(page).toHaveTitle('Admin — Scheduler | iChrisBirch')
    await expect(page.locator('.admin-subnav__link--active', { hasText: 'Scheduler' })).toBeVisible()

    await page.locator('.admin-subnav__link', { hasText: 'Users' }).click()
    await expect(page).toHaveTitle('Admin — Users | iChrisBirch')

    await page.locator('.admin-subnav__link', { hasText: 'Config' }).click()
    await expect(page).toHaveTitle('Admin — Config | iChrisBirch')

    await page.locator('.admin-subnav__link', { hasText: 'System Health' }).click()
    await expect(page).toHaveTitle('Admin — System | iChrisBirch')
  })

  test('sidebar shows active state on admin pages', async ({ page }) => {
    await page.goto('/admin')
    await expect(page.locator('.nav-link--active', { hasText: 'Admin' })).toBeVisible()
  })
})

test.describe('Admin Scheduler Page', () => {
  test('loads scheduler page with heading', async ({ page }) => {
    await page.goto('/admin/scheduler')
    await expect(page).toHaveTitle('Admin — Scheduler | iChrisBirch')
    await expect(page.locator('h2', { hasText: 'Scheduler Jobs' })).toBeVisible()
  })
})

test.describe('Admin Users Page', () => {
  // Users list endpoint (GET /users/) is outside /admin/* path,
  // so the admin authelia sim doesn't apply. Users page loads
  // but can't fetch data in test env. Data verification tested
  // via Python API tests and dev environment.
  test('loads users page with heading', async ({ page }) => {
    await page.goto('/admin/users')
    await expect(page).toHaveTitle('Admin — Users | iChrisBirch')
    await expect(page.locator('h2', { hasText: 'Users' })).toBeVisible()
  })
})

test.describe('Admin Config Page', () => {
  test('loads config page with sections', async ({ page }) => {
    await page.goto('/admin/config')
    await expect(page).toHaveTitle('Admin — Config | iChrisBirch')
    await expect(page.locator('h2', { hasText: 'Environment Configuration' })).toBeVisible()
    await expect(page.locator('.config-section').first()).toBeVisible({ timeout: 10000 })
  })

  test('secrets are masked in config display', async ({ page }) => {
    await page.goto('/admin/config')
    await expect(page.locator('.config-section').first()).toBeVisible({ timeout: 10000 })
    // Open auth section
    await page.locator('.config-section summary', { hasText: 'Auth' }).click()
    await expect(page.locator('.config-entry__value--masked').first()).toBeVisible()
  })
})
