import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

/** Helper: open the add duration modal, fill in fields, and submit */
async function createDuration(
  page: import('@playwright/test').Page,
  name: string,
  startDate = '2020-01-01',
) {
  await page.getByTestId('duration-add-button').click()
  await expect(page.getByTestId('add-edit-modal')).toBeVisible({ timeout: 5000 })
  await page.getByTestId('duration-name-input').fill(name)
  await page.getByTestId('duration-start-date-input').locator('input').fill(startDate)
  await page.getByTestId('duration-name-input').press('Enter')
  await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
}

// Smoke tests only — interaction-heavy tests (edit, expand notes, compare
// mode, filter/sort) are covered by component integration tests in
// src/views/__tests__/DurationsView.test.ts

test.describe('Durations Page', () => {
  test('API calls succeed through Traefik routing (CORS check)', async ({ page }) => {
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/durations')
    await expect(page.locator('.grid')).toBeVisible({ timeout: 10000 })
    await expect(page.locator(ERROR)).not.toBeVisible()
    expect(apiErrors).toEqual([])
  })

  test('loads the page and displays the duration list', async ({ page }) => {
    await page.goto('/durations')
    await expect(page).toHaveTitle('Durations | iChrisBirch')
    await expect(page.locator('.grid')).toBeVisible()
  })

  test('creates a new duration and verifies it appears in the list', async ({ page }) => {
    await page.goto('/durations')

    const name = `E2E Create ${Date.now()}`
    await createDuration(page, name)
    await expect(page.locator(SUCCESS).first()).toContainText('added')

    await expect(page.getByTestId('duration-item').filter({ hasText: name })).toBeVisible()
  })

  test('deletes a duration and verifies it is removed', async ({ page }) => {
    await page.goto('/durations')

    const name = `E2E Delete ${Date.now()}`
    await createDuration(page, name, '2021-06-15')

    const targetItem = page.getByTestId('duration-item').filter({ hasText: name })
    await expect(targetItem).toBeVisible()
    await targetItem.getByTestId('duration-delete-button').click()

    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
    await expect(targetItem).not.toBeVisible()
  })

  test('duration card shows add note form', async ({ page }) => {
    await page.goto('/durations')

    const name = `E2E Notes ${Date.now()}`
    await createDuration(page, name, '2022-03-01')

    const targetItem = page.getByTestId('duration-item').filter({ hasText: name })
    await expect(targetItem).toBeVisible()
    await expect(targetItem.locator('.duration-card__add-note')).toBeVisible()

    // Clean up
    await targetItem.getByTestId('duration-delete-button').click()
    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
  })

  test('sidebar navigation to durations works', async ({ page }) => {
    await page.goto('/durations')
    await expect(page).toHaveTitle('Durations | iChrisBirch')

    const sidebarLink = page.locator('.nav-link--active', { hasText: 'Durations' })
    await expect(sidebarLink).toBeVisible()
  })
})
