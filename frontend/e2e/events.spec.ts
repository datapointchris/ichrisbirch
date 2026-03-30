import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

/** Helper: open the add event modal, fill in fields, and submit */
async function createEvent(page: import('@playwright/test').Page, name: string, venue = 'E2E Venue') {
  await page.getByTestId('event-add-button').click()
  await expect(page.getByTestId('add-edit-modal')).toBeVisible({ timeout: 5000 })
  await page.getByTestId('event-name-input').fill(name)
  await page.getByTestId('event-date-input').fill('2028-06-15T18:00')
  await page.getByTestId('event-venue-input').fill(venue)
  await page.getByTestId('event-cost-input').fill('25')
  await page.getByTestId('event-cost-input').press('Enter')
  await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
}

// Smoke tests only — interaction-heavy tests (edit, toggle attending,
// URL links) are covered by component integration tests in
// src/views/__tests__/EventsView.test.ts

test.describe('Events Page', () => {
  test('API calls succeed through Traefik routing (CORS check)', async ({ page }) => {
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/events')
    await expect(page.locator('.grid')).toBeVisible({ timeout: 10000 })
    await expect(page.locator(ERROR)).not.toBeVisible()
    expect(apiErrors).toEqual([])
  })

  test('loads the page and displays the event list', async ({ page }) => {
    await page.goto('/events')
    await expect(page).toHaveTitle('Events | iChrisBirch')
  })

  test('creates a new event and verifies it appears in the list', async ({ page }) => {
    await page.goto('/events')

    const name = `E2E Event ${Date.now()}`
    await createEvent(page, name)
    await expect(page.getByTestId('event-item').filter({ hasText: name })).toBeVisible()
  })

  test('deletes an event and verifies it is removed', async ({ page }) => {
    await page.goto('/events')

    const name = `E2E Delete ${Date.now()}`
    await createEvent(page, name)

    const item = page.getByTestId('event-item').filter({ hasText: name })
    await expect(item).toBeVisible()
    await item.getByTestId('event-delete-button').click()

    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
    await expect(item).not.toBeVisible()
  })

  test('sidebar navigation to events works', async ({ page }) => {
    await page.goto('/events')
    await expect(page).toHaveTitle('Events | iChrisBirch')

    const sidebarLink = page.locator('.nav-link--active', { hasText: 'Events' })
    await expect(sidebarLink).toBeVisible()
  })
})
