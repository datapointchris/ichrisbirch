import { test, expect } from '@playwright/test'

// E2E tests run as user@icb.com (regular user, not admin).
// Admin API endpoints return 403, so data sections won't render.
// These tests verify page structure, routing, and navigation.

test.describe('Admin Page Structure', () => {
  test('loads admin page with layout and subnav', async ({ page }) => {
    await page.goto('/admin')
    await expect(page).toHaveTitle('Admin — System | iChrisBirch')
    await expect(page.locator('h1', { hasText: 'Admin' })).toBeVisible()
  })

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

  test('sidebar shows active state on admin pages', async ({ page }) => {
    await page.goto('/admin')
    const sidebarLink = page.locator('.nav-link--active', { hasText: 'Admin' })
    await expect(sidebarLink).toBeVisible()
  })
})

test.describe('Admin Sub-navigation', () => {
  test('navigates to scheduler tab', async ({ page }) => {
    await page.goto('/admin')
    await page.locator('.admin-subnav__link', { hasText: 'Scheduler' }).click()
    await expect(page).toHaveTitle('Admin — Scheduler | iChrisBirch')
    await expect(page.locator('.admin-subnav__link--active', { hasText: 'Scheduler' })).toBeVisible()
  })

  test('navigates to users tab', async ({ page }) => {
    await page.goto('/admin')
    await page.locator('.admin-subnav__link', { hasText: 'Users' }).click()
    await expect(page).toHaveTitle('Admin — Users | iChrisBirch')
  })

  test('navigates to config tab', async ({ page }) => {
    await page.goto('/admin')
    await page.locator('.admin-subnav__link', { hasText: 'Config' }).click()
    await expect(page).toHaveTitle('Admin — Config | iChrisBirch')
  })

  test('navigates back to system health from other tabs', async ({ page }) => {
    await page.goto('/admin/scheduler')
    await page.locator('.admin-subnav__link', { hasText: 'System Health' }).click()
    await expect(page).toHaveTitle('Admin — System | iChrisBirch')
    await expect(page.locator('.admin-subnav__link--active', { hasText: 'System Health' })).toBeVisible()
  })
})

test.describe('Admin Scheduler Page', () => {
  test('loads scheduler page with heading', async ({ page }) => {
    await page.goto('/admin/scheduler')
    await expect(page).toHaveTitle('Admin — Scheduler | iChrisBirch')
    await expect(page.locator('h1', { hasText: 'Admin' })).toBeVisible()
  })
})

test.describe('Admin Users Page', () => {
  test('loads users page with heading', async ({ page }) => {
    await page.goto('/admin/users')
    await expect(page).toHaveTitle('Admin — Users | iChrisBirch')
    await expect(page.locator('h2', { hasText: 'Users' })).toBeVisible()
  })
})

test.describe('Admin Config Page', () => {
  test('loads config page with heading', async ({ page }) => {
    await page.goto('/admin/config')
    await expect(page).toHaveTitle('Admin — Config | iChrisBirch')
    await expect(page.locator('h2', { hasText: 'Environment Configuration' })).toBeVisible()
  })
})
