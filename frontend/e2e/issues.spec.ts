import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

/** Helper: open the file issue modal, fill in the one required field, and submit */
async function fileIssue(page: import('@playwright/test').Page, title: string) {
  await page.getByTestId('issue-add-button').click()
  // The page also mounts the cancel modal, so the shared modal id matches twice.
  await expect(page.getByTestId('issue-title-input')).toBeVisible({ timeout: 5000 })
  await page.getByTestId('issue-title-input').fill(title)
  await page.getByTestId('issue-submit-button').click()
  await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
}

// Smoke tests only. The interaction-heavy cases live in component tests:
// src/views/__tests__/IssuesView.test.ts covers the lenses, the filters, the
// row actions and the ranking buttons;
// src/views/__tests__/AddEditIssueModal.test.ts covers the form's payloads;
// src/views/__tests__/IssueDetailPanel.test.ts covers dependencies and comments;
// src/views/__tests__/CancelIssueModal.test.ts covers the cancel payload; and
// src/views/__tests__/IssueViews.test.ts covers the initiatives and labels pages.

test.describe('Issues Page', () => {
  test('API calls succeed through Traefik routing (CORS check)', async ({ page }) => {
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/issues')
    await expect(page.getByTestId('issues-header')).toBeVisible({ timeout: 10000 })
    await expect(page.locator(ERROR)).not.toBeVisible()
    expect(apiErrors).toEqual([])
  })

  test('loads the page and displays the title', async ({ page }) => {
    await page.goto('/issues')
    await expect(page).toHaveTitle('Issues | iChrisBirch')
    await expect(page.getByTestId('issues-header')).toBeVisible()
  })

  test('files an issue, then deletes it', async ({ page }) => {
    await page.goto('/issues')
    await expect(page.getByTestId('issues-header')).toBeVisible({ timeout: 10000 })

    const title = `E2E Issue ${Date.now()}`
    await fileIssue(page, title)

    const row = page.getByTestId('issue-item').filter({ hasText: title })
    await expect(row).toBeVisible()
    await row.getByTestId('issue-delete-button').click()

    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
    await expect(row).not.toBeVisible()
  })

  test('the initiatives page loads through its own route', async ({ page }) => {
    await page.goto('/issues/initiatives')
    await expect(page).toHaveTitle('Initiatives | iChrisBirch')
    await expect(page.getByTestId('initiatives-header')).toBeVisible({ timeout: 10000 })
    await expect(page.locator(ERROR)).not.toBeVisible()
  })

  test('the labels page loads through its own route', async ({ page }) => {
    await page.goto('/issues/labels')
    await expect(page).toHaveTitle('Issue Labels | iChrisBirch')
    await expect(page.getByTestId('issue-labels-header')).toBeVisible({ timeout: 10000 })
    await expect(page.locator(ERROR)).not.toBeVisible()
  })

  test('sidebar navigation to issues works', async ({ page }) => {
    await page.goto('/issues')
    await expect(page).toHaveTitle('Issues | iChrisBirch')

    const sidebarLink = page.getByTestId('sidebar-/issues')
    await expect(sidebarLink).toBeVisible()
    await expect(sidebarLink).toHaveAttribute('data-active', 'true')
  })
})
