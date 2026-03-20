import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

test.describe('Books Page', () => {
  test('API calls succeed through Traefik routing (CORS check)', async ({ page }) => {
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/books')

    // Wait for the table header to appear — this means the API GET succeeded
    await expect(page.locator('.books__header')).toBeVisible({ timeout: 10000 })

    // No error notifications should be visible
    await expect(page.locator(ERROR)).not.toBeVisible()

    // No structured error logs should have been emitted
    expect(apiErrors).toEqual([])
  })

  test('loads the page and displays the title', async ({ page }) => {
    await page.goto('/books')
    await expect(page).toHaveTitle('Books | iChrisBirch')
    await expect(page.locator('.books__header')).toBeVisible()
  })

  test('info bar is visible with status counters', async ({ page }) => {
    await page.goto('/books')
    await expect(page.locator('.task-layout__info')).toBeVisible()
    await expect(page.locator('.book--read.book-filter')).toBeVisible()
    await expect(page.locator('.book--reading.book-filter')).toBeVisible()
    await expect(page.locator('.book--unread.book-filter')).toBeVisible()
    await expect(page.locator('.book--abandoned.book-filter')).toBeVisible()
    await expect(page.locator('.book--total.book-filter')).toBeVisible()
  })

  test('add form has required fields', async ({ page }) => {
    await page.goto('/books')
    await expect(page.locator('.add-item-wrapper')).toBeVisible()
    await expect(page.locator('#title')).toBeVisible()
    await expect(page.locator('#author')).toBeVisible()
    await expect(page.locator('#tags')).toBeVisible()

    await expect(page.locator('#title')).toHaveAttribute('required', '')
    await expect(page.locator('#author')).toHaveAttribute('required', '')
    await expect(page.locator('#tags')).toHaveAttribute('required', '')
  })

  test('creates a new book and verifies it appears in the table', async ({ page }) => {
    await page.goto('/books')
    await expect(page.locator('.books__header')).toBeVisible({ timeout: 10000 })

    const title = `E2E Book ${Date.now()}`

    await page.fill('#title', title)
    await page.fill('#author', 'E2E Author')
    await page.fill('#tags', 'test, e2e')
    await page.locator('.add-item-wrapper button[type="submit"]').click()

    // Verify success notification appears
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
    await expect(page.locator(SUCCESS).first()).toContainText('added')

    // Verify the book appears in the table
    await expect(page.locator('.books__row', { hasText: title })).toBeVisible()
  })

  test('deletes a book and verifies it is removed', async ({ page }) => {
    await page.goto('/books')
    await expect(page.locator('.books__header')).toBeVisible({ timeout: 10000 })

    const title = `E2E Delete ${Date.now()}`

    await page.fill('#title', title)
    await page.fill('#author', 'Delete Author')
    await page.fill('#tags', 'delete, test')
    await page.locator('.add-item-wrapper button[type="submit"]').click()
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })

    // Find and delete it
    const targetRow = page.locator('.books__row', { hasText: title })
    await expect(targetRow).toBeVisible()
    await targetRow.locator('.button--hidden').click()

    // Verify deletion notification
    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })

    // Verify it's gone from the table
    await expect(targetRow).not.toBeVisible()
  })

  test('sidebar navigation to books works', async ({ page }) => {
    await page.goto('/books')
    await expect(page).toHaveTitle('Books | iChrisBirch')

    const sidebarLink = page.locator('.nav-link--active', { hasText: 'Books' })
    await expect(sidebarLink).toBeVisible()
  })
})
