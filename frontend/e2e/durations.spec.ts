import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

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

  test('add duration form is present with all fields', async ({ page }) => {
    await page.goto('/durations')
    await expect(page.locator('.add-item-wrapper')).toBeVisible()
    await expect(page.locator('#name')).toBeVisible()
    await expect(page.locator('#start_date')).toBeVisible()
    await expect(page.locator('#end_date')).toBeVisible()
    await expect(page.locator('#notes')).toBeVisible()
    await expect(page.locator('.color-picker')).toBeVisible()
  })

  test('creates a new duration and verifies it appears in the list', async ({ page }) => {
    await page.goto('/durations')

    const name = `E2E Create ${Date.now()}`

    await page.fill('#name', name)
    await page.fill('#start_date', '2020-01-01')
    await page.fill('#notes', 'Created by Playwright')
    await page.click('button[type="submit"]')

    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
    await expect(page.locator(SUCCESS).first()).toContainText('added')

    await expect(page.locator('.grid__item', { hasText: name })).toBeVisible()
  })

  test('deletes a duration and verifies it is removed', async ({ page }) => {
    await page.goto('/durations')

    const name = `E2E Delete ${Date.now()}`

    await page.fill('#name', name)
    await page.fill('#start_date', '2021-06-15')
    await page.click('button[type="submit"]')
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })

    // Expand the card to access delete button
    const targetItem = page.locator('.grid__item', { hasText: name })
    await expect(targetItem).toBeVisible()
    await targetItem.locator('.duration-card__header').click()

    await targetItem.locator('.button--danger').click()

    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
    await expect(targetItem).not.toBeVisible()
  })

  test('expands a duration card to see notes section', async ({ page }) => {
    await page.goto('/durations')

    // Create a duration
    const name = `E2E Expand ${Date.now()}`
    await page.fill('#name', name)
    await page.fill('#start_date', '2022-03-01')
    await page.click('button[type="submit"]')
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })

    const targetItem = page.locator('.grid__item', { hasText: name })
    await expect(targetItem).toBeVisible()

    // Click to expand
    await targetItem.locator('.duration-card__header').click()

    // Should see the add note form inside
    await expect(targetItem.locator('.duration-card__add-note')).toBeVisible()

    // Clean up
    await targetItem.locator('.button--danger').click()
    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
  })

  test('required field validation', async ({ page }) => {
    await page.goto('/durations')

    const nameField = page.locator('#name')
    const startDateField = page.locator('#start_date')
    await expect(nameField).toHaveAttribute('required', '')
    await expect(startDateField).toHaveAttribute('required', '')
  })

  test('sidebar navigation to durations works', async ({ page }) => {
    await page.goto('/durations')
    await expect(page).toHaveTitle('Durations | iChrisBirch')

    const sidebarLink = page.locator('.nav-link--active', { hasText: 'Durations' })
    await expect(sidebarLink).toBeVisible()
  })
})
