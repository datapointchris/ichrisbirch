import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

/** Helper: open the add book modal, fill in required fields, and submit */
async function createBook(page: import('@playwright/test').Page, title: string, author = 'E2E Author') {
  await page.getByTestId('book-add-button').click()
  await expect(page.getByTestId('add-edit-modal')).toBeVisible({ timeout: 5000 })
  await page.getByTestId('book-title-input').fill(title)
  await page.getByTestId('book-author-input').fill(author)
  await page.getByTestId('book-tags-input').fill('test, e2e')
  await page.getByTestId('book-tags-input').press('Enter')
  await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
}

// Smoke tests only — interaction-heavy tests (edit, search, sort,
// filter, expand detail) are covered by component integration tests
// in src/views/__tests__/BooksView.test.ts

test.describe('Books Page', () => {
  test('API calls succeed through Traefik routing (CORS check)', async ({ page }) => {
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/books')
    await expect(page.locator('.books__header')).toBeVisible({ timeout: 10000 })
    await expect(page.locator(ERROR)).not.toBeVisible()
    expect(apiErrors).toEqual([])
  })

  test('loads the page and displays the title', async ({ page }) => {
    await page.goto('/books')
    await expect(page).toHaveTitle('Books | iChrisBirch')
    await expect(page.locator('.books__header')).toBeVisible()
  })

  test('creates a new book and verifies it appears in the table', async ({ page }) => {
    await page.goto('/books')
    await expect(page.locator('.books__header')).toBeVisible({ timeout: 10000 })

    const title = `E2E Book ${Date.now()}`
    await createBook(page, title)
    await expect(page.getByTestId('book-item').filter({ hasText: title })).toBeVisible()
  })

  test('deletes a book and verifies it is removed', async ({ page }) => {
    await page.goto('/books')
    await expect(page.locator('.books__header')).toBeVisible({ timeout: 10000 })

    const title = `E2E Delete ${Date.now()}`
    await createBook(page, title)

    const row = page.getByTestId('book-item').filter({ hasText: title })
    await expect(row).toBeVisible()
    await row.getByTestId('book-delete-button').click()

    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
    await expect(row).not.toBeVisible()
  })

  test('info bar is visible with status counters', async ({ page }) => {
    await page.goto('/books')
    await expect(page.locator('.task-layout__info')).toBeVisible()
  })

  test('sidebar navigation to books works', async ({ page }) => {
    await page.goto('/books')
    await expect(page).toHaveTitle('Books | iChrisBirch')

    const sidebarLink = page.locator('.nav-link--active', { hasText: 'Books' })
    await expect(sidebarLink).toBeVisible()
  })
})
