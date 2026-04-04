import { test, expect } from '@playwright/test'

// Smoke tests only — these sub-pages are form-based and already minimal.
// Main article CRUD is covered by component integration tests in
// src/views/__tests__/ArticlesView.test.ts

test.describe('Article Insights Page', () => {
  test('loads the page and displays the form', async ({ page }) => {
    await page.goto('/articles/insights')
    await expect(page).toHaveTitle('Article Insights | iChrisBirch')
    await expect(page.locator('h3', { hasText: 'URL' })).toBeVisible()
    await expect(page.locator('#url')).toBeVisible()
    await expect(page.locator('button', { hasText: 'Educate Me!' })).toBeVisible()
  })

  test('subnav shows insights as active', async ({ page }) => {
    await page.goto('/articles/insights')
    await expect(page.getByTestId('articles-subnav-insights')).toHaveClass(/subnav__link--active/)
  })
})

test.describe('Article Bulk Import Page', () => {
  test('loads the page and displays the form', async ({ page }) => {
    await page.goto('/articles/bulk-import')
    await expect(page).toHaveTitle('Bulk Import Articles | iChrisBirch')
    await expect(page.locator('h2', { hasText: 'Bulk Add New Articles' })).toBeVisible()
    await expect(page.locator('#text')).toBeVisible()
    await expect(page.locator('button', { hasText: 'Add New Articles' })).toBeVisible()
  })

  test('subnav shows bulk-import as active', async ({ page }) => {
    await page.goto('/articles/bulk-import')
    await expect(page.getByTestId('articles-subnav-bulk-import')).toHaveClass(/subnav__link--active/)
  })
})
