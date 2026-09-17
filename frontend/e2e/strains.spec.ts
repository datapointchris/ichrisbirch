import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

/** Helper: open the add strain modal, fill in the one required field, and submit */
async function createStrain(page: import('@playwright/test').Page, name: string) {
  await page.getByTestId('strain-add-button').click()
  await expect(page.getByTestId('add-edit-modal')).toBeVisible({ timeout: 5000 })
  await page.getByTestId('strain-name-input').fill(name)
  await page.getByTestId('strain-submit-button').click()
  await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
}

// Smoke tests only. The interaction-heavy cases live in component tests:
// src/views/__tests__/StrainsView.test.ts covers the table, the detail panel,
// the counters and the filter wiring, and
// src/views/__tests__/AddEditStrainModal.test.ts covers the edit form and the
// descriptor chips, including the payload each one produces.

test.describe('Strains Page', () => {
  test('API calls succeed through Traefik routing (CORS check)', async ({ page }) => {
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/strains')
    await expect(page.getByTestId('strains-header')).toBeVisible({ timeout: 10000 })
    await expect(page.locator(ERROR)).not.toBeVisible()
    expect(apiErrors).toEqual([])
  })

  test('loads the page and displays the title', async ({ page }) => {
    await page.goto('/strains')
    await expect(page).toHaveTitle('Strains | iChrisBirch')
    await expect(page.getByTestId('strains-header')).toBeVisible()
  })

  test('creates a new strain and verifies it appears in the table', async ({ page }) => {
    await page.goto('/strains')
    await expect(page.getByTestId('strains-header')).toBeVisible({ timeout: 10000 })

    const name = `E2E Strain ${Date.now()}`
    await createStrain(page, name)
    await expect(page.getByTestId('strain-item').filter({ hasText: name })).toBeVisible()
  })

  test('deletes a strain and verifies it is removed', async ({ page }) => {
    await page.goto('/strains')
    await expect(page.getByTestId('strains-header')).toBeVisible({ timeout: 10000 })

    const name = `E2E Delete ${Date.now()}`
    await createStrain(page, name)

    const row = page.getByTestId('strain-item').filter({ hasText: name })
    await expect(row).toBeVisible()
    await row.getByTestId('strain-delete-button').click()

    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
    await expect(row).not.toBeVisible()
  })

  test('the vocabulary reaches the page, so a descriptor can be chosen', async ({ page }) => {
    await page.goto('/strains')
    await expect(page.getByTestId('strains-header')).toBeVisible({ timeout: 10000 })

    await page.getByTestId('strain-add-button').click()
    await expect(page.getByTestId('add-edit-modal')).toBeVisible({ timeout: 5000 })
    // The chips are built from GET /strains/vocabulary/, so one rendering here
    // proves the endpoint answered and the list was not empty.
    await expect(page.getByTestId('strain-effect-relaxed')).toBeVisible()
  })

  test('info bar is visible with status counters', async ({ page }) => {
    await page.goto('/strains')
    await expect(page.getByTestId('strains-info')).toBeVisible()
  })

  test('sidebar navigation to strains works', async ({ page }) => {
    await page.goto('/strains')
    await expect(page).toHaveTitle('Strains | iChrisBirch')

    const sidebarLink = page.getByTestId('sidebar-/strains')
    await expect(sidebarLink).toBeVisible()
    await expect(sidebarLink).toHaveAttribute('data-active', 'true')
  })
})
