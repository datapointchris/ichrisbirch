import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

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

  test('add form is present with all fields', async ({ page }) => {
    await page.goto('/articles')
    await expect(page.locator('.add-item-wrapper')).toBeVisible()
    await expect(page.locator('#url')).toBeVisible()
    await expect(page.locator('#title')).toBeVisible()
    await expect(page.locator('#tags')).toBeVisible()
    await expect(page.locator('#summary')).toBeVisible()
    await expect(page.locator('#notes')).toBeVisible()
  })

  test('search bar is present', async ({ page }) => {
    await page.goto('/articles')
    await expect(page.locator('.articles__search')).toBeVisible()
  })

  test('creates a new article and verifies it appears', async ({ page }) => {
    await page.goto('/articles')

    const articleTitle = `E2E Article ${Date.now()}`

    await page.fill('#url', `https://example.com/e2e-${Date.now()}`)
    await page.fill('#title', articleTitle)
    await page.fill('#tags', 'e2e, testing')
    await page.fill('#summary', 'This article was created by Playwright E2E tests.')
    await page.locator('.add-item-wrapper button', { hasText: 'Add Article' }).click()

    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
    await expect(page.locator(SUCCESS).first()).toContainText('Article added')

    await expect(page.locator('.articles__row', { hasText: articleTitle })).toBeVisible()
  })

  test('deletes an article and verifies it is removed', async ({ page }) => {
    await page.goto('/articles')

    const articleTitle = `E2E Delete ${Date.now()}`

    await page.fill('#url', `https://example.com/e2e-delete-${Date.now()}`)
    await page.fill('#title', articleTitle)
    await page.fill('#tags', 'e2e, delete')
    await page.fill('#summary', 'This article will be deleted.')
    await page.locator('.add-item-wrapper button', { hasText: 'Add Article' }).click()
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })

    const targetRow = page.locator('.articles__row', { hasText: articleTitle })
    await expect(targetRow).toBeVisible()
    await targetRow.locator('.button--hidden').click()

    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
    await expect(targetRow).not.toBeVisible()
  })

  test('toggles favorite status on an article', async ({ page }) => {
    await page.goto('/articles')

    const articleTitle = `E2E Favorite ${Date.now()}`

    await page.fill('#url', `https://example.com/e2e-fav-${Date.now()}`)
    await page.fill('#title', articleTitle)
    await page.fill('#tags', 'e2e, favorite')
    await page.fill('#summary', 'Testing favorite toggle.')
    await page.locator('.add-item-wrapper button', { hasText: 'Add Article' }).click()
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })

    const targetRow = page.locator('.articles__row', { hasText: articleTitle })
    await expect(targetRow).toBeVisible()

    // Initially not favorite — star is inactive
    const star = targetRow.locator('.articles__star')
    await expect(star).toBeVisible()
    await expect(star).not.toHaveClass(/articles__star--active/)
    await star.click()

    // After toggle — star should be active (favorite)
    await expect(star).toHaveClass(/articles__star--active/, { timeout: 5000 })

    // Clean up
    await targetRow.locator('.button--hidden').click()
    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
  })

  test('archive removes article from list', async ({ page }) => {
    await page.goto('/articles')
    await expect(page.locator('.articles__header')).toBeVisible({ timeout: 10000 })

    const title = `E2E Archive ${Date.now()}`
    await page.fill('#url', `https://example.com/e2e-archive-${Date.now()}`)
    await page.fill('#title', title)
    await page.fill('#tags', 'e2e, archive')
    await page.fill('#summary', 'Testing archive.')
    await page.locator('.add-item-wrapper button', { hasText: 'Add Article' }).click()
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })

    const row = page.locator('.articles__row', { hasText: title })
    await expect(row).toBeVisible()

    // Expand and archive
    await row.locator('.articles__chevron').click()
    await expect(page.locator('.articles__detail--open')).toBeVisible()
    await page.locator('.articles__detail--open button', { hasText: 'Archive' }).click()
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
    await expect(row).not.toBeVisible({ timeout: 5000 })
  })

  test('mark read removes article from list', async ({ page }) => {
    await page.goto('/articles')
    await expect(page.locator('.articles__header')).toBeVisible({ timeout: 10000 })

    const title = `E2E Read ${Date.now()}`
    await page.fill('#url', `https://example.com/e2e-read-${Date.now()}`)
    await page.fill('#title', title)
    await page.fill('#tags', 'e2e, read')
    await page.fill('#summary', 'Testing mark read.')
    await page.locator('.add-item-wrapper button', { hasText: 'Add Article' }).click()
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })

    const row = page.locator('.articles__row', { hasText: title })
    await expect(row).toBeVisible()

    // Expand and mark read
    await row.locator('.articles__chevron').click()
    await expect(page.locator('.articles__detail--open')).toBeVisible()
    await page.locator('.articles__detail--open button', { hasText: 'Mark Read' }).click()
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
    await expect(row).not.toBeVisible({ timeout: 5000 })
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
