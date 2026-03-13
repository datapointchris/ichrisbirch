import { test, expect } from '@playwright/test'

// Notification selectors matching the NotificationToast component's actual CSS classes
const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

test.describe('Events Page', () => {
  test('API calls succeed through Traefik routing (CORS check)', async ({ page }) => {
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/events')

    // Wait for the grid to appear — this means the API GET succeeded
    await expect(page.locator('.grid')).toBeVisible({ timeout: 10000 })

    // No error notifications should be visible
    await expect(page.locator(ERROR)).not.toBeVisible()

    // No structured error logs should have been emitted
    expect(apiErrors).toEqual([])
  })

  test('loads the page and displays the event list', async ({ page }) => {
    await page.goto('/events')
    await expect(page).toHaveTitle('Events | iChrisBirch')
    await expect(page.locator('.grid')).toBeVisible()
  })

  test('add event form is present with all fields', async ({ page }) => {
    await page.goto('/events')
    await expect(page.locator('.add-item-wrapper')).toBeVisible()
    await expect(page.locator('#name')).toBeVisible()
    await expect(page.locator('#date')).toBeVisible()
    await expect(page.locator('#venue')).toBeVisible()
    await expect(page.locator('#url')).toBeVisible()
    await expect(page.locator('#cost')).toBeVisible()
    await expect(page.locator('#attending')).toBeVisible()
    await expect(page.locator('#notes')).toBeVisible()
  })

  test('creates a new event and verifies it appears in the list', async ({ page }) => {
    await page.goto('/events')

    const name = `E2E Create ${Date.now()}`

    await page.fill('#name', name)
    await page.fill('#date', '2028-06-15T19:00')
    await page.fill('#venue', 'Test Venue')
    await page.fill('#url', 'https://example.com/event')
    await page.fill('#cost', '25.00')
    await page.fill('#notes', 'Created by Playwright')
    await page.click('button[type="submit"]')

    // Verify success notification appears
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
    await expect(page.locator(SUCCESS).first()).toContainText('Event added')

    // Verify the event appears in the grid
    await expect(page.locator('.grid__item', { hasText: name })).toBeVisible()
  })

  test('deletes an event and verifies it is removed', async ({ page }) => {
    await page.goto('/events')

    const name = `E2E Delete ${Date.now()}`

    await page.fill('#name', name)
    await page.fill('#date', '2028-12-31T20:00')
    await page.fill('#venue', 'Delete Venue')
    await page.fill('#cost', '0')
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

  test('toggles attending on then off', async ({ page }) => {
    await page.goto('/events')

    const name = `E2E Attend ${Date.now()}`

    // Create event without attending
    await page.fill('#name', name)
    await page.fill('#date', '2028-08-20T18:00')
    await page.fill('#venue', 'Attend Venue')
    await page.fill('#cost', '10')
    await page.click('button[type="submit"]')
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })

    const targetItem = page.locator('.grid__item', { hasText: name })
    await expect(targetItem).toBeVisible()

    // Should NOT be highlighted (not attending)
    await expect(targetItem).not.toHaveClass(/grid__item--highlighted/)

    // Click "Attend Event" button
    await targetItem.locator('button', { hasText: 'Attend Event' }).click()
    await expect(page.locator(SUCCESS, { hasText: 'Attending' })).toBeVisible({ timeout: 5000 })

    // Should now be highlighted
    await expect(targetItem).toHaveClass(/grid__item--highlighted/)

    // Click "Attending" button to toggle off
    await targetItem.locator('button', { hasText: 'Attending' }).click()
    await expect(page.locator(SUCCESS, { hasText: 'No longer attending' })).toBeVisible({ timeout: 5000 })

    // Should no longer be highlighted
    await expect(targetItem).not.toHaveClass(/grid__item--highlighted/)

    // Clean up
    await targetItem.locator('.button--danger').click()
    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
  })

  test('required field validation', async ({ page }) => {
    await page.goto('/events')

    const nameField = page.locator('#name')
    const dateField = page.locator('#date')
    const venueField = page.locator('#venue')
    const costField = page.locator('#cost')

    await expect(nameField).toHaveAttribute('required', '')
    await expect(dateField).toHaveAttribute('required', '')
    await expect(venueField).toHaveAttribute('required', '')
    await expect(costField).toHaveAttribute('required', '')
  })

  test('sidebar navigation to events works', async ({ page }) => {
    await page.goto('/events')
    await expect(page).toHaveTitle('Events | iChrisBirch')

    // Verify the sidebar link is marked active
    const sidebarLink = page.locator('.nav-link--active', { hasText: 'Events' })
    await expect(sidebarLink).toBeVisible()
  })
})
