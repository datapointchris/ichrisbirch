import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

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

  test('displays the add autotask form', async ({ page }) => {
    await page.goto('/autotasks')
    await expect(page.locator('h2', { hasText: 'Add New AutoTask' })).toBeVisible()
    await expect(page.locator('#name')).toBeVisible()
    await expect(page.locator('#priority')).toBeVisible()
    await expect(page.locator('#category')).toBeVisible()
    await expect(page.locator('#frequency')).toBeVisible()
  })

  test('creates a new autotask', async ({ page }) => {
    await page.goto('/autotasks')
    await expect(page.locator('.grid')).toBeVisible({ timeout: 10000 })

    await page.fill('#name', 'E2E Test AutoTask')
    await page.fill('#priority', '5')
    await page.selectOption('#category', 'Chore')
    await page.selectOption('#frequency', 'Weekly')
    await page.fill('#notes', 'Created by Playwright')

    await page.locator('button', { hasText: 'Add New Autotask' }).click()
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
    await expect(page.locator('.grid__item h2', { hasText: 'E2E Test AutoTask' }).first()).toBeVisible()
  })

  test('deletes an autotask', async ({ page }) => {
    await page.goto('/autotasks')
    await expect(page.locator('.grid')).toBeVisible({ timeout: 10000 })

    // Create one to delete
    await page.fill('#name', 'E2E Delete AutoTask')
    await page.fill('#priority', '1')
    await page.selectOption('#category', 'Chore')
    await page.selectOption('#frequency', 'Daily')
    await page.locator('button', { hasText: 'Add New Autotask' }).click()
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })

    // Delete it
    const card = page.locator('.grid__item', { hasText: 'E2E Delete AutoTask' })
    await card.locator('button', { hasText: 'Delete Autotask' }).click()
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
    await expect(card).not.toBeVisible()
  })

  test('runs an autotask and verifies success', async ({ page }) => {
    await page.goto('/autotasks')
    await expect(page.locator('.grid')).toBeVisible({ timeout: 10000 })

    // Create one to run
    const name = `E2E Run ${Date.now()}`
    await page.fill('#name', name)
    await page.fill('#priority', '10')
    await page.selectOption('#category', 'Home')
    await page.selectOption('#frequency', 'Monthly')
    await page.locator('button', { hasText: 'Add New Autotask' }).click()
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })

    // Run it
    const card = page.locator('.grid__item', { hasText: name })
    await expect(card).toBeVisible()
    await card.locator('button', { hasText: 'Run Autotask Now' }).click()
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })

    // Autotask should still be on the page (run doesn't delete it)
    await expect(card).toBeVisible()

    // Run count should show 2 (1 from create + 1 from manual run)
    const runCountItem = card.locator('.item-details__item', { hasText: 'Run Count' })
    await expect(runCountItem.locator('.item-details__item-content')).toHaveText('2')
  })

  test('sidebar navigation to autotasks works', async ({ page }) => {
    await page.goto('/autotasks')
    await expect(page).toHaveTitle('AutoTasks | iChrisBirch')
    const sidebarLink = page.locator('.nav-link--active', { hasText: 'AutoTasks' })
    await expect(sidebarLink).toBeVisible()
  })
})
