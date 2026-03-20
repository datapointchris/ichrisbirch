import { test, expect } from '@playwright/test'

test.describe('Dashboard Page', () => {
  test('loads the page and displays the title', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page).toHaveTitle('Dashboard | iChrisBirch')
    await expect(page.locator('.vuedash__title', { hasText: 'Dashboard' })).toBeVisible()
  })

  test('displays the widget grid', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page.locator('.vuedash__grid')).toBeVisible({ timeout: 10000 })
  })

  test('add widget button opens the widget picker', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page.locator('.vuedash__title')).toBeVisible()

    await page.locator('button', { hasText: 'Add Widget' }).click()
    await expect(page.locator('.widget-picker')).toBeVisible()
    await expect(page.locator('.widget-picker h3', { hasText: 'Add Widget' })).toBeVisible()

    // Verify widget options are listed
    await expect(page.locator('.widget-picker__item').first()).toBeVisible()

    // Close the picker
    await page.locator('.widget-picker button', { hasText: 'Close' }).click()
    await expect(page.locator('.widget-picker')).not.toBeVisible()
  })

  test('sidebar navigation to dashboard works', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page).toHaveTitle('Dashboard | iChrisBirch')

    const sidebarLink = page.locator('.nav-link--active', { hasText: 'Dashboard' })
    await expect(sidebarLink).toBeVisible()
  })
})
