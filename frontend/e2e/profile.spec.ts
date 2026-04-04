import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'

// Smoke tests only — interaction-heavy tests (swatch count, API key CRUD,
// reset priorities) are covered by component integration tests in
// src/views/__tests__/ProfileViews.test.ts

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
    await expect(page.getByTestId('profile-subnav-profile')).toHaveClass(/subnav__link--active/)

    // Navigate to settings
    await page.getByTestId('profile-subnav-settings').click()
    await expect(page).toHaveTitle('Settings | iChrisBirch', { timeout: 5000 })
    await expect(page.getByTestId('profile-subnav-settings')).toHaveClass(/subnav__link--active/)

    // Navigate back to profile
    await page.getByTestId('profile-subnav-profile').click()
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

  test('clicking a theme color swatch saves preference', async ({ page }) => {
    await page.goto('/profile/settings')
    await page.locator('.theme-colors__swatch[title="Blue"]').click()
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
  })
})
