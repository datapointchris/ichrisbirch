import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

/** Helper: open the add countdown modal, fill in fields, and submit */
async function createCountdown(
  page: import('@playwright/test').Page,
  name: string,
  dueDate = '2028-06-15',
) {
  await page.getByTestId('countdown-add-button').click()
  await expect(page.getByTestId('add-edit-modal')).toBeVisible({ timeout: 5000 })
  await page.getByTestId('countdown-name-input').fill(name)
  await page.getByTestId('countdown-due-date-input').locator('input').fill(dueDate)
  await page.getByTestId('countdown-submit-button').click()
  await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
}

// Smoke tests only — interaction-heavy tests (edit, modal fields,
// urgency classes) are covered by component integration tests in
// src/views/__tests__/CountdownsView.test.ts

test.describe('Countdowns Page', () => {
  test('API calls succeed through Traefik routing (CORS check)', async ({ page }) => {
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/countdowns')
    await expect(page.locator('.grid')).toBeVisible({ timeout: 10000 })
    await expect(page.locator(ERROR)).not.toBeVisible()
    expect(apiErrors).toEqual([])
  })

  test('loads the page and displays the countdown list', async ({ page }) => {
    await page.goto('/countdowns')
    await expect(page).toHaveTitle('Countdowns | iChrisBirch')
  })

  test('creates a new countdown and verifies it appears in the list', async ({ page }) => {
    await page.goto('/countdowns')

    const name = `E2E Create ${Date.now()}`
    await createCountdown(page, name)
    await expect(page.getByTestId('countdown-item').filter({ hasText: name })).toBeVisible()
  })

  test('deletes a countdown and verifies it is removed', async ({ page }) => {
    await page.goto('/countdowns')

    const name = `E2E Delete ${Date.now()}`
    await createCountdown(page, name, '2028-12-31')

    const targetItem = page.getByTestId('countdown-item').filter({ hasText: name })
    await expect(targetItem).toBeVisible()
    await targetItem.getByTestId('countdown-delete-button').click()

    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
    await expect(targetItem).not.toBeVisible()
  })

  test('sidebar navigation to countdowns works', async ({ page }) => {
    await page.goto('/countdowns')
    await expect(page).toHaveTitle('Countdowns | iChrisBirch')

    const sidebarLink = page.locator('.nav-link--active', { hasText: 'Countdowns' })
    await expect(sidebarLink).toBeVisible()
  })
})
