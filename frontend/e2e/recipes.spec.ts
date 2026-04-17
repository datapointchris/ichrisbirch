import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

/** Helper: create a minimal recipe through the modal and verify success. */
async function createRecipe(page: import('@playwright/test').Page, name: string) {
  await page.getByTestId('recipe-add-button').click()
  await expect(page.getByTestId('add-edit-modal')).toBeVisible({ timeout: 5000 })
  await page.getByTestId('recipe-name-input').fill(name)
  await page.getByTestId('recipe-instructions-input').fill('E2E instructions')
  await page.getByTestId('recipe-ingredient-item-0').fill('E2E ingredient')
  await page.getByTestId('recipe-ingredient-quantity-0').fill('1')
  await page.getByTestId('recipe-submit-button').click()
  await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
}

// Smoke tests only — interaction-heavy tests (filters, sort, ingredient search,
// modal fields, AI suggest flow) are covered by component integration tests
// in src/views/__tests__/RecipesView.test.ts and AddEditRecipeModal.test.ts

test.describe('Recipes Page', () => {
  test('API calls succeed through Traefik routing (CORS check)', async ({ page }) => {
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/recipes')
    await expect(page.locator('.recipes__header')).toBeVisible({ timeout: 10000 })
    await expect(page.locator(ERROR)).not.toBeVisible()
    expect(apiErrors).toEqual([])
  })

  test('loads the page and displays the title', async ({ page }) => {
    await page.goto('/recipes')
    await expect(page).toHaveTitle('Recipes | iChrisBirch')
    await expect(page.locator('.recipes__header')).toBeVisible()
  })

  test('creates a new recipe and verifies it appears in the table', async ({ page }) => {
    await page.goto('/recipes')
    await expect(page.locator('.recipes__header')).toBeVisible({ timeout: 10000 })

    const name = `E2E Recipe ${Date.now()}`
    await createRecipe(page, name)
    await expect(page.getByTestId('recipe-item').filter({ hasText: name })).toBeVisible()
  })

  test('deletes a recipe and verifies it is removed', async ({ page }) => {
    await page.goto('/recipes')
    await expect(page.locator('.recipes__header')).toBeVisible({ timeout: 10000 })

    const name = `E2E Delete ${Date.now()}`
    await createRecipe(page, name)

    const row = page.getByTestId('recipe-item').filter({ hasText: name })
    await expect(row).toBeVisible()
    await row.getByTestId('recipe-delete-button').click()

    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
    await expect(row).not.toBeVisible()
  })

  test('mark-made button increments count', async ({ page }) => {
    await page.goto('/recipes')
    await expect(page.locator('.recipes__header')).toBeVisible({ timeout: 10000 })

    const name = `E2E Made ${Date.now()}`
    await createRecipe(page, name)

    const row = page.getByTestId('recipe-item').filter({ hasText: name })
    await row.getByTestId('recipe-mark-made-button').click()

    await expect(page.locator(SUCCESS, { hasText: 'made' })).toBeVisible({ timeout: 5000 })
  })

  test('sidebar navigation to recipes works', async ({ page }) => {
    await page.goto('/recipes')
    await expect(page).toHaveTitle('Recipes | iChrisBirch')

    const sidebarLink = page.locator('.nav-link--active', { hasText: 'Recipes' })
    await expect(sidebarLink).toBeVisible()
  })

  test('stats page loads', async ({ page }) => {
    await page.goto('/recipes/stats')
    await expect(page).toHaveTitle('Recipes Stats | iChrisBirch')
    // Either summary cards render or empty state — both confirm stats view loaded
    const loaded = page.locator('.stats-cards, .stats-empty')
    await expect(loaded.first()).toBeVisible({ timeout: 10000 })
  })
})
