import { test, expect } from '@playwright/test'

const ERROR = '.flash-messages__message--error'

// Smoke tests only — dragging, inline rename, collapse and undo are covered by
// component integration tests in src/views/__tests__/ShoppingView.test.ts.
// The `phone` project in playwright.config.ts runs this file at phone size too.

test.describe('Shopping Page', () => {
  test('API calls succeed through Traefik routing (CORS check)', async ({ page }) => {
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/shopping')
    await expect(page.getByTestId('shopping-add-input')).toBeVisible({ timeout: 10000 })
    await expect(page.locator(ERROR)).not.toBeVisible()
    expect(apiErrors).toEqual([])
  })

  test('loads the page', async ({ page }) => {
    await page.goto('/shopping')
    await expect(page).toHaveTitle('Shopping | iChrisBirch')
  })

  test('adds an item, then checking it off moves it to bought today', async ({ page }) => {
    await page.goto('/shopping')

    const name = `e2e item ${Date.now()}`
    await page.getByTestId('shopping-add-input').fill(name)
    await page.getByTestId('shopping-add-input').press('Enter')

    const row = page.getByTestId('shopping-item').filter({ hasText: name })
    await expect(row).toBeVisible({ timeout: 5000 })
    await row.getByTestId('shopping-item-check').click()

    await expect(row).not.toBeVisible({ timeout: 5000 })
    await expect(page.getByTestId('shopping-bought-row').filter({ hasText: name })).toBeVisible()
  })

  test('sidebar navigation to shopping works', async ({ page, isMobile }) => {
    await page.goto('/shopping')
    if (isMobile) await page.getByTestId('sidebar-open-button').click()

    await expect(page.locator('.nav-link--active', { hasText: 'Shopping' })).toBeVisible()
  })
})
