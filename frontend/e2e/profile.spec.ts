import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'

test.describe('Profile Page', () => {
  test('loads the profile page and displays user info', async ({ page }) => {
    await page.goto('/profile')
    await expect(page).toHaveTitle('Profile | iChrisBirch')
    await expect(page.locator('h2', { hasText: 'Profile' })).toBeVisible()
    await expect(page.locator('dt', { hasText: 'Name' })).toBeVisible()
    await expect(page.locator('dt', { hasText: 'Email' })).toBeVisible()
    await expect(page.locator('dt', { hasText: 'Role' })).toBeVisible()
  })

  test('subnav navigation works between profile and settings', async ({ page }) => {
    await page.goto('/profile')
    await expect(page.locator('.profile-subnav__link--active', { hasText: 'Profile' })).toBeVisible()

    // Navigate to settings
    await page.locator('.profile-subnav__link', { hasText: 'Settings' }).click()
    await expect(page).toHaveTitle('Settings | iChrisBirch', { timeout: 5000 })
    await expect(page.locator('.profile-subnav__link--active', { hasText: 'Settings' })).toBeVisible()

    // Navigate back to profile
    await page.locator('.profile-subnav__link', { hasText: 'Profile' }).click()
    await expect(page).toHaveTitle('Profile | iChrisBirch', { timeout: 5000 })
  })

  test('sidebar shows active state on profile pages', async ({ page }) => {
    await page.goto('/profile')
    const sidebarLink = page.locator('.nav-link--active', { hasText: 'Profile' })
    await expect(sidebarLink).toBeVisible()
  })
})

test.describe('Profile Settings Page', () => {
  test('loads with all three sections visible', async ({ page }) => {
    await page.goto('/profile/settings')
    await expect(page).toHaveTitle('Settings | iChrisBirch')
    await expect(page.locator('h3', { hasText: 'Appearance' })).toBeVisible()
    await expect(page.locator('h3', { hasText: 'Personal API Keys' })).toBeVisible()
    await expect(page.locator('h3', { hasText: 'Actions' })).toBeVisible()
  })

  test('theme color swatches render', async ({ page }) => {
    await page.goto('/profile/settings')
    const swatches = page.locator('.theme-colors__swatch')
    // 9 color themes + 12 named themes = 21 total
    await expect(swatches).toHaveCount(21)
  })

  test('clicking a theme color swatch saves preference', async ({ page }) => {
    await page.goto('/profile/settings')
    await page.locator('.theme-colors__swatch[title="Blue"]').click()
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
  })

  test('creates an API key and shows the key banner', async ({ page }) => {
    await page.goto('/profile/settings')
    const keyName = `E2E Key ${Date.now()}`

    await page.fill('#key-name', keyName)
    await page.locator('button[type="submit"]', { hasText: 'Create API Key' }).click()

    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
    await expect(page.locator('.api-key-banner')).toBeVisible()
    await expect(page.locator('.api-keys-table td', { hasText: keyName })).toBeVisible()
  })

  test('reset task priorities button works', async ({ page }) => {
    await page.goto('/profile/settings')
    await page.locator('button', { hasText: 'Reset Task Priorities' }).click()
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
  })
})
