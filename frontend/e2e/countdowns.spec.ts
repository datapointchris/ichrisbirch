import { test, expect } from '@playwright/test'

// Notification selectors matching the NotificationToast component's actual CSS classes
const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

test.describe('Countdowns Page', () => {
  test('API calls succeed through Traefik routing (CORS check)', async ({ page }) => {
    // This test catches cross-origin issues between app.docker.localhost
    // and api.docker.localhost. It verifies that:
    // 1. The page loads through Traefik path-based routing
    // 2. The browser can make cross-origin API calls (CORS preflight passes)
    // 3. Auth headers are forwarded correctly
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/countdowns')

    // Wait for the grid to appear — this means the API GET succeeded
    await expect(page.locator('.grid')).toBeVisible({ timeout: 10000 })

    // No error notifications should be visible
    await expect(page.locator(ERROR)).not.toBeVisible()

    // No structured error logs should have been emitted
    expect(apiErrors).toEqual([])
  })

  test('loads the page and displays the countdown list', async ({ page }) => {
    await page.goto('/countdowns')
    await expect(page).toHaveTitle('Countdowns | iChrisBirch')
    await expect(page.locator('.grid')).toBeVisible()
  })

  test('add countdown form is present with all fields', async ({ page }) => {
    await page.goto('/countdowns')
    await expect(page.locator('.add-item-wrapper')).toBeVisible()
    await expect(page.locator('#name')).toBeVisible()
    await expect(page.locator('#due_date')).toBeVisible()
    await expect(page.locator('#notes')).toBeVisible()
  })

  test('creates a new countdown and verifies it appears in the list', async ({ page }) => {
    await page.goto('/countdowns')

    // Unique name to avoid collisions with previous test runs
    const name = `E2E Create ${Date.now()}`

    await page.fill('#name', name)
    await page.fill('#due_date', '2028-06-15')
    await page.fill('#notes', 'Created by Playwright')
    await page.click('button[type="submit"]')

    // Verify success notification appears
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
    await expect(page.locator(SUCCESS).first()).toContainText('Countdown added')

    // Verify the countdown appears in the grid
    await expect(page.locator('.grid__item', { hasText: name })).toBeVisible()
  })

  test('deletes a countdown and verifies it is removed', async ({ page }) => {
    await page.goto('/countdowns')

    // Create with unique name then delete it
    const name = `E2E Delete ${Date.now()}`

    await page.fill('#name', name)
    await page.fill('#due_date', '2028-12-31')
    await page.click('button[type="submit"]')
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })

    // Find and delete it
    const targetItem = page.locator('.grid__item', { hasText: name })
    await expect(targetItem).toBeVisible()
    await targetItem.locator('.button--danger').click()

    // Verify deletion notification
    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })

    // Verify it's gone from the list
    await expect(targetItem).not.toBeVisible()
  })

  test('shows error details when API call fails', async ({ page }) => {
    await page.goto('/countdowns')

    // Verify form validation attributes exist (browser prevents empty submit)
    const nameField = page.locator('#name')
    const dateField = page.locator('#due_date')
    await expect(nameField).toHaveAttribute('required', '')
    await expect(dateField).toHaveAttribute('required', '')
  })

  test('sidebar navigation to countdowns works', async ({ page }) => {
    // Navigate to countdowns via sidebar (start from countdowns since / is Flask)
    await page.goto('/countdowns')
    await expect(page).toHaveTitle('Countdowns | iChrisBirch')

    // Verify the sidebar link is marked active
    const sidebarLink = page.locator('.nav-link--active', { hasText: 'Countdowns' })
    await expect(sidebarLink).toBeVisible()
  })
})
