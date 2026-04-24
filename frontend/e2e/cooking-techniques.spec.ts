import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

// Smoke tests only — interaction-heavy tests (filters, modal fields, sort)
// are covered by component tests in src/views/__tests__/CookingTechniquesView.test.ts

test.describe('Cooking Techniques Page', () => {
  test('API calls succeed through Traefik routing (CORS check)', async ({ page }) => {
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/recipes/cooking-techniques')
    await expect(page.locator('.cooking-techniques__header')).toBeVisible({ timeout: 10000 })
    await expect(page.locator(ERROR)).not.toBeVisible()
    expect(apiErrors).toEqual([])
  })

  test('loads the page and displays the title', async ({ page }) => {
    await page.goto('/recipes/cooking-techniques')
    await expect(page).toHaveTitle('Cooking Techniques | iChrisBirch')
    await expect(page.locator('.cooking-techniques__header')).toBeVisible()
  })

  test('subnav navigation from Recipes works', async ({ page }) => {
    await page.goto('/recipes')
    await page.getByTestId('recipes-subnav-techniques').click()
    await expect(page).toHaveURL(/\/recipes\/cooking-techniques/)
    await expect(page.locator('.cooking-techniques__header')).toBeVisible({ timeout: 5000 })
  })

  test('creates a technique and verifies it appears in the list', async ({ page }) => {
    await page.goto('/recipes/cooking-techniques')
    await expect(page.locator('.cooking-techniques__header')).toBeVisible({ timeout: 10000 })

    const name = `E2E Technique ${Date.now()}`

    await page.getByTestId('cooking-technique-add-button').click()
    await expect(page.getByTestId('add-edit-modal')).toBeVisible({ timeout: 5000 })

    await page.getByTestId('cooking-technique-name-input').fill(name)
    await page.getByTestId('cooking-technique-category-input').click()
    await page.getByTestId('cooking-technique-category-input-option-heat_application').click()
    await page.getByTestId('cooking-technique-summary-input').fill('E2E summary')
    await page.getByTestId('cooking-technique-body-input').fill('## E2E heading\n\nMarkdown body.')
    await page.getByTestId('cooking-technique-submit-button').click()

    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
    await expect(page.getByTestId('cooking-technique-item').filter({ hasText: name })).toBeVisible()
  })
})
