import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

test.describe('Money Wasted Page', () => {
  test('API calls succeed through Traefik routing (CORS check)', async ({ page }) => {
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/money-wasted')
    await expect(page.locator('.grid')).toBeVisible({ timeout: 10000 })
    await expect(page.locator(ERROR)).not.toBeVisible()
    expect(apiErrors).toEqual([])
  })

  test('loads the page and displays the total and table header', async ({ page }) => {
    await page.goto('/money-wasted')
    await expect(page).toHaveTitle('Money Wasted | iChrisBirch')
    await expect(page.locator('.money-wasted--total')).toBeVisible()
    await expect(page.locator('.money-wasted__header')).toBeVisible()
  })

  test('add form is present with all fields', async ({ page }) => {
    await page.goto('/money-wasted')
    await expect(page.locator('.add-item-wrapper')).toBeVisible()
    await expect(page.locator('#item')).toBeVisible()
    await expect(page.locator('#amount')).toBeVisible()
    await expect(page.locator('#date_purchased')).toBeVisible()
    await expect(page.locator('#date_wasted')).toBeVisible()
    await expect(page.locator('#notes')).toBeVisible()
  })

  test('creates a new entry and verifies it appears in the list', async ({ page }) => {
    await page.goto('/money-wasted')

    const itemName = `E2E Create ${Date.now()}`

    await page.fill('#item', itemName)
    await page.fill('#amount', '42.50')
    await page.fill('#date_wasted', '2026-03-14')
    await page.fill('#notes', 'Created by Playwright')
    await page.click('button[type="submit"]')

    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
    await expect(page.locator(SUCCESS).first()).toContainText('Money wasted entry added')

    await expect(page.locator('.money-wasted__row', { hasText: itemName })).toBeVisible()
  })

  test('deletes an entry and verifies it is removed', async ({ page }) => {
    await page.goto('/money-wasted')

    const itemName = `E2E Delete ${Date.now()}`

    await page.fill('#item', itemName)
    await page.fill('#amount', '10.00')
    await page.fill('#date_wasted', '2026-03-14')
    await page.click('button[type="submit"]')
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })

    const targetRow = page.locator('.money-wasted__row', { hasText: itemName })
    await expect(targetRow).toBeVisible()
    await targetRow.locator('.button--hidden').click()

    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
    await expect(targetRow).not.toBeVisible()
  })

  test('sidebar navigation to money wasted works', async ({ page }) => {
    await page.goto('/money-wasted')
    await expect(page).toHaveTitle('Money Wasted | iChrisBirch')

    const sidebarLink = page.locator('.nav-link--active', { hasText: 'Money Wasted' })
    await expect(sidebarLink).toBeVisible()
  })
})
