import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

/** Helper: open the add autotask modal, fill in fields, and submit */
async function createAutoTask(page: import('@playwright/test').Page, name: string, priority = '5') {
  await page.getByTestId('autotask-add-button').click()
  await expect(page.getByTestId('add-edit-modal')).toBeVisible({ timeout: 5000 })
  await page.getByTestId('autotask-name-input').fill(name)
  await page.getByTestId('autotask-priority-input').fill(priority)
  await page.getByTestId('autotask-category-input').click()
  await page.getByTestId('autotask-category-input-option-Chore').click()
  await page.getByTestId('autotask-frequency-input').click()
  await page.getByTestId('autotask-frequency-input-option-Weekly').click()
  await page.getByTestId('autotask-priority-input').press('Enter')
  await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
}

// Smoke tests only — interaction-heavy tests (edit, modal fields, run
// autotask, run count) are covered by component integration tests in
// src/views/__tests__/AutoTasksView.test.ts

test.describe('AutoTasks Page', () => {
  test('API calls succeed through Traefik routing (CORS check)', async ({ page }) => {
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/autotasks')
    await expect(page.locator('.grid')).toBeVisible({ timeout: 10000 })
    await expect(page.locator(ERROR)).not.toBeVisible()
    expect(apiErrors).toEqual([])
  })

  test('loads the page and displays the title', async ({ page }) => {
    await page.goto('/autotasks')
    await expect(page).toHaveTitle('AutoTasks | iChrisBirch')
  })

  test('creates a new autotask', async ({ page }) => {
    await page.goto('/autotasks')
    await expect(page.locator('.grid')).toBeVisible({ timeout: 10000 })

    const name = `E2E AutoTask ${Date.now()}`
    await createAutoTask(page, name)
    await expect(page.getByTestId('autotask-item').filter({ hasText: name }).first()).toBeVisible()
  })

  test('deletes an autotask', async ({ page }) => {
    await page.goto('/autotasks')
    await expect(page.locator('.grid')).toBeVisible({ timeout: 10000 })

    const name = `E2E Delete ${Date.now()}`
    await createAutoTask(page, name)

    const card = page.getByTestId('autotask-item').filter({ hasText: name })
    await expect(card).toBeVisible()
    await expect(page.locator(SUCCESS).first()).not.toBeVisible({ timeout: 15000 })
    await card.getByTestId('autotask-delete-button').click()
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
    await expect(card).not.toBeVisible()
  })

  test('sidebar navigation to autotasks works', async ({ page }) => {
    await page.goto('/autotasks')
    await expect(page).toHaveTitle('AutoTasks | iChrisBirch')
    const sidebarLink = page.locator('.nav-link--active', { hasText: 'AutoTasks' })
    await expect(sidebarLink).toBeVisible()
  })
})
