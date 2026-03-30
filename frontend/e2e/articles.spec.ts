import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

/** Helper: open the add article modal, fill in fields, and submit */
async function createArticle(page: import('@playwright/test').Page, title: string, url?: string) {
  const articleUrl = url ?? `https://example.com/e2e-${Date.now()}`
  await page.getByTestId('article-add-button').click()
  await expect(page.getByTestId('add-edit-modal')).toBeVisible({ timeout: 5000 })
  await page.getByTestId('article-url-input').fill(articleUrl)
  await page.getByTestId('article-title-input').fill(title)
  await page.getByTestId('article-tags-input').fill('e2e, testing')
  await page.getByTestId('article-summary-input').fill('Created by Playwright E2E tests.')
  await page.getByTestId('article-title-input').press('Enter')
  await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
}

// Smoke tests only — interaction-heavy tests (edit, favorite toggle,
// archive, mark read, search) are covered by component integration
// tests in src/views/__tests__/ArticlesView.test.ts

test.describe('Articles Page', () => {
  test('API calls succeed through Traefik routing (CORS check)', async ({ page }) => {
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/articles')
    await expect(page.locator('.articles__header')).toBeVisible({ timeout: 10000 })
    await expect(page.locator(ERROR)).not.toBeVisible()
    expect(apiErrors).toEqual([])
  })

  test('loads the page with correct title', async ({ page }) => {
    await page.goto('/articles')
    await expect(page).toHaveTitle('Articles | iChrisBirch')
  })

  test('creates a new article and verifies it appears', async ({ page }) => {
    await page.goto('/articles')

    const articleTitle = `E2E Article ${Date.now()}`
    await createArticle(page, articleTitle)
    await expect(page.locator(SUCCESS).first()).toContainText('added')

    await expect(page.getByTestId('article-item').filter({ hasText: articleTitle })).toBeVisible()
  })

  test('deletes an article and verifies it is removed', async ({ page }) => {
    await page.goto('/articles')

    const articleTitle = `E2E Delete ${Date.now()}`
    await createArticle(page, articleTitle)

    const targetRow = page.getByTestId('article-item').filter({ hasText: articleTitle })
    await expect(targetRow).toBeVisible()
    await targetRow.getByTestId('article-delete-button').click()

    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
    await expect(targetRow).not.toBeVisible()
  })

  test('subnav links are present', async ({ page }) => {
    await page.goto('/articles')
    await expect(page.locator('.articles-subnav__link', { hasText: 'All Articles' })).toBeVisible()
    await expect(page.locator('.articles-subnav__link', { hasText: 'Bulk Import' })).toBeVisible()
    await expect(page.locator('.articles-subnav__link', { hasText: 'Insights' })).toBeVisible()
  })

  test('sidebar navigation to articles works', async ({ page }) => {
    await page.goto('/articles')
    await expect(page).toHaveTitle('Articles | iChrisBirch')

    const sidebarLink = page.locator('.nav-link--active', { hasText: 'Articles' })
    await expect(sidebarLink).toBeVisible()
  })
})
