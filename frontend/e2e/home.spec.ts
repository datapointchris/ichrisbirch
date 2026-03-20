import { test, expect } from '@playwright/test'

test.describe('Home Page', () => {
  test('loads the page and displays heading', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveTitle('Home | iChrisBirch')
    await expect(page.locator('h1', { hasText: 'Chris Birch' })).toBeVisible()
    await expect(page.locator('h2', { hasText: 'Data Engineer' })).toBeVisible()
  })

  test('displays project links', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('.home-link-label', { hasText: 'Code' })).toBeVisible()
    await expect(page.locator('.home-link-label', { hasText: 'Chat' })).toBeVisible()
    await expect(page.locator('.home-link-label', { hasText: 'API' })).toBeVisible()
    await expect(page.locator('.home-link-label', { hasText: 'Docs' })).toBeVisible()
  })

  test('links open in new tabs', async ({ page }) => {
    await page.goto('/')
    // Wait for at least one link to render
    await expect(page.locator('.home-links a').first()).toBeVisible()
    const links = page.locator('.home-links a')
    await expect(links).toHaveCount(4)

    for (let i = 0; i < 4; i++) {
      await expect(links.nth(i)).toHaveAttribute('target', '_blank')
    }
  })
})
