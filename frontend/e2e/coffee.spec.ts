import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

// Smoke tests only. The interaction-heavy cases live in component tests:
// src/views/__tests__/CoffeeViews.test.ts covers both pages' cards, filters,
// sorting and modal wiring.

test.describe('Coffee Shops Page', () => {
  test('API calls succeed through Traefik routing (CORS check)', async ({ page }) => {
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/coffee/shops')
    await expect(page.getByTestId('add-shop-button')).toBeVisible({ timeout: 10000 })
    await expect(page.locator(ERROR)).not.toBeVisible()
    expect(apiErrors).toEqual([])
  })

  test('loads the page and displays the title', async ({ page }) => {
    await page.goto('/coffee/shops')
    await expect(page).toHaveTitle('Coffee Shops | iChrisBirch')
  })

  test('adds a shop, then deletes it', async ({ page }) => {
    await page.goto('/coffee/shops')
    await expect(page.getByTestId('add-shop-button')).toBeVisible({ timeout: 10000 })

    const name = `E2E Shop ${Date.now()}`
    await page.getByTestId('add-shop-button').click()
    await expect(page.getByTestId('add-edit-modal')).toBeVisible({ timeout: 5000 })
    await page.getByTestId('shop-name-input').fill(name)
    await page.getByTestId('shop-submit-button').click()
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })

    const card = page.getByTestId('shop-card').filter({ hasText: name })
    await expect(card).toBeVisible()
    await card.getByTestId('shop-delete-button').click()

    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
    await expect(card).not.toBeVisible()
  })

  test('sidebar navigation to coffee works', async ({ page }) => {
    await page.goto('/coffee/shops')
    const sidebarLink = page.getByTestId('sidebar-/coffee/shops')
    await expect(sidebarLink).toBeVisible()
    await expect(sidebarLink).toHaveAttribute('data-active', 'true')
  })
})

test.describe('Coffee Beans Page', () => {
  test('loads the page and displays the title', async ({ page }) => {
    await page.goto('/coffee/beans')
    await expect(page).toHaveTitle('Coffee Beans | iChrisBirch')
    await expect(page.getByTestId('add-bean-button')).toBeVisible({ timeout: 10000 })
    await expect(page.locator(ERROR)).not.toBeVisible()
  })

  test('adds a bean, then deletes it', async ({ page }) => {
    await page.goto('/coffee/beans')
    await expect(page.getByTestId('add-bean-button')).toBeVisible({ timeout: 10000 })

    const name = `E2E Bean ${Date.now()}`
    await page.getByTestId('add-bean-button').click()
    await expect(page.getByTestId('add-edit-modal')).toBeVisible({ timeout: 5000 })
    await page.getByTestId('bean-name-input').fill(name)
    await page.getByTestId('bean-submit-button').click()
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })

    const card = page.getByTestId('bean-card').filter({ hasText: name })
    await expect(card).toBeVisible()
    await card.getByTestId('bean-delete-button').click()

    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
    await expect(card).not.toBeVisible()
  })
})
