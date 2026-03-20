import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

/** Helper: open the add money wasted modal, fill in fields, and submit */
async function createMoneyWasted(page: import('@playwright/test').Page, item: string, amount = '25.00') {
  await page.getByTestId('mw-add-button').click()
  await expect(page.getByTestId('add-edit-modal')).toBeVisible({ timeout: 5000 })
  await page.getByTestId('mw-item-input').fill(item)
  await page.getByTestId('mw-amount-input').fill(amount)
  await page.getByTestId('mw-date-wasted-input').locator('input').fill('2026-01-15')
  await page.getByTestId('mw-amount-input').press('Enter')
  await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
}

test.describe('Money Wasted Page', () => {
  test('API calls succeed through Traefik routing (CORS check)', async ({ page }) => {
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/money-wasted')
    await expect(page.locator('.money-wasted--total')).toBeVisible({ timeout: 10000 })
    await expect(page.locator(ERROR)).not.toBeVisible()
    expect(apiErrors).toEqual([])
  })

  test('loads the page and displays the total', async ({ page }) => {
    await page.goto('/money-wasted')
    await expect(page).toHaveTitle('Money Wasted | iChrisBirch')
    await expect(page.locator('.money-wasted--total')).toBeVisible()
  })

  test('creates a new entry and verifies it appears in the list', async ({ page }) => {
    await page.goto('/money-wasted')

    const item = `E2E Waste ${Date.now()}`
    await createMoneyWasted(page, item, '42.50')
    await expect(page.getByTestId('mw-item').filter({ hasText: item })).toBeVisible()
  })

  test('deletes an entry and verifies it is removed', async ({ page }) => {
    await page.goto('/money-wasted')

    const item = `E2E Delete ${Date.now()}`
    await createMoneyWasted(page, item)

    const row = page.getByTestId('mw-item').filter({ hasText: item })
    await expect(row).toBeVisible()
    await row.getByTestId('mw-delete-button').click()

    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
    await expect(row).not.toBeVisible()
  })

  test('sidebar navigation to money wasted works', async ({ page }) => {
    await page.goto('/money-wasted')
    await expect(page).toHaveTitle('Money Wasted | iChrisBirch')

    const sidebarLink = page.locator('.nav-link--active', { hasText: 'Money Wasted' })
    await expect(sidebarLink).toBeVisible()
  })
})
