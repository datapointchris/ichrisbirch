import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

test.describe('Profile Page', () => {
  test('API calls succeed through Traefik routing (CORS check)', async ({ page }) => {
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/profile')
    await expect(page.locator('.grid')).toBeVisible({ timeout: 10000 })
    await expect(page.locator(ERROR)).not.toBeVisible()
    expect(apiErrors).toEqual([])
  })

  test('loads the profile page and displays user info', async ({ page }) => {
    await page.goto('/profile')
    await expect(page).toHaveTitle('Profile | iChrisBirch')
    await expect(page.locator('h2', { hasText: 'Profile' })).toBeVisible()
    // User info should be displayed
    await expect(page.locator('dt', { hasText: 'Name' })).toBeVisible()
    await expect(page.locator('dt', { hasText: 'Email' })).toBeVisible()
    await expect(page.locator('dt', { hasText: 'Role' })).toBeVisible()
  })

  test('subnav navigation works between profile and settings', async ({ page }) => {
    await page.goto('/profile')
    await expect(page.locator('.profile-subnav__link--active', { hasText: 'Profile' })).toBeVisible()

    // Navigate to settings
    await page.click('.profile-subnav__link', { hasText: 'Settings' } as never)
    await expect(page).toHaveTitle('Settings | iChrisBirch')
    await expect(page.locator('.profile-subnav__link--active', { hasText: 'Settings' })).toBeVisible()

    // Navigate back to profile
    await page.click('.profile-subnav__link', { hasText: 'Profile' } as never)
    await expect(page).toHaveTitle('Profile | iChrisBirch')
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
    await expect(swatches).toHaveCount(9)
  })

  test('clicking a theme color swatch saves preference', async ({ page }) => {
    await page.goto('/profile/settings')
    // Click the blue swatch
    await page.click('.theme-colors__swatch[title="blue"]')
    await expect(page.locator(SUCCESS, { hasText: 'Theme color set to blue' })).toBeVisible({ timeout: 5000 })
  })

  test('creates an API key and shows the key banner', async ({ page }) => {
    await page.goto('/profile/settings')
    const keyName = `E2E Key ${Date.now()}`

    await page.fill('#key-name', keyName)
    await page.click('button[type="submit"]', { hasText: 'Create API Key' } as never)

    await expect(page.locator(SUCCESS, { hasText: 'API key created' })).toBeVisible({ timeout: 5000 })
    await expect(page.locator('.api-key-banner')).toBeVisible()
    // Key should appear in the table
    await expect(page.locator('.api-keys-table td', { hasText: keyName })).toBeVisible()
  })

  test('reset task priorities button works', async ({ page }) => {
    await page.goto('/profile/settings')
    await page.click('button', { hasText: 'Reset Task Priorities' } as never)
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
  })
})
