import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

test.describe('Habits Page', () => {
  test('Daily page loads with CORS working and subnav present', async ({ page }) => {
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/habits')
    await expect(page).toHaveTitle('Daily Habits | iChrisBirch')

    // Subnav links present
    await expect(page.locator('a', { hasText: 'Daily Habits' })).toBeVisible()
    await expect(page.locator('a', { hasText: 'Completed' })).toBeVisible()
    await expect(page.locator('a', { hasText: 'Manage' })).toBeVisible()

    // No CORS or API errors
    await expect(page.locator(ERROR)).not.toBeVisible()
    expect(apiErrors).toEqual([])
  })

  test('Manage page: create category then create habit', async ({ page }) => {
    await page.goto('/habits/manage')
    await expect(page).toHaveTitle('Manage Habits | iChrisBirch')

    // Wait for page load
    await expect(page.locator('h3', { hasText: 'Current Categories' })).toBeVisible({ timeout: 10000 })

    // Create a unique category
    const catName = `E2E Cat ${Date.now()}`
    await page.fill('#category-name', catName)
    await page.locator('button[type="submit"]', { hasText: 'Add Category' }).click()
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })

    // Create a habit in the new category
    const habitName = `E2E Habit ${Date.now()}`
    await page.fill('#habit-name', habitName)
    await page.locator('#habit-category').selectOption({ label: catName })
    await page.locator('button[type="submit"]', { hasText: 'Add Habit' }).click()
    await expect(page.locator(SUCCESS, { hasText: 'Habit added' })).toBeVisible({ timeout: 5000 })

    // Verify habit appears in current habits
    await expect(page.locator('.habits-manage__row', { hasText: habitName })).toBeVisible()
  })

  test('Daily page: complete a habit moves it to done', async ({ page }) => {
    await page.goto('/habits')

    // Wait for the daily columns to load
    const todoColumn = page.locator('.habits__column').first()
    await expect(todoColumn).toBeVisible({ timeout: 10000 })

    // If there are todo habits, complete the first one
    const firstCheck = page.locator('.habits__check').first()
    if (await firstCheck.isVisible({ timeout: 3000 }).catch(() => false)) {
      const habitName = await page.locator('.habits__item-name').first().textContent()
      await firstCheck.click()
      await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })

      // Verify it appears in done column
      if (habitName) {
        await expect(
          page.locator('.habits__item--done', { hasText: habitName })
        ).toBeVisible({ timeout: 5000 })
      }
    }
  })

  test('Completed page: filter and chart renders', async ({ page }) => {
    await page.goto('/habits/completed')
    await expect(page).toHaveTitle('Completed Habits | iChrisBirch')

    // Radio buttons visible
    await expect(page.locator('label', { hasText: 'This Week' })).toBeVisible({ timeout: 10000 })
    await expect(page.locator('label', { hasText: 'Last 30' })).toBeVisible()

    // Select "All" filter and apply
    await page.locator('label', { hasText: 'All' }).click()
    await page.locator('button', { hasText: 'Filter' }).click()

    // Either chart or "no completed" message should appear
    const chartOrEmpty = page.locator('canvas, .habits-completed__count--empty')
    await expect(chartOrEmpty.first()).toBeVisible({ timeout: 10000 })
  })

  test('Subnav navigation between sub-pages works', async ({ page }) => {
    await page.goto('/habits')
    await expect(page).toHaveTitle('Daily Habits | iChrisBirch')

    // Navigate to Completed
    await page.locator('a', { hasText: 'Completed' }).click()
    await expect(page).toHaveTitle('Completed Habits | iChrisBirch')

    // Navigate to Manage
    await page.locator('a', { hasText: 'Manage' }).click()
    await expect(page).toHaveTitle('Manage Habits | iChrisBirch')

    // Back to Daily
    await page.locator('a', { hasText: 'Daily Habits' }).click()
    await expect(page).toHaveTitle('Daily Habits | iChrisBirch')
  })

  test('sidebar navigation to habits works', async ({ page }) => {
    await page.goto('/habits')
    await expect(page).toHaveTitle('Daily Habits | iChrisBirch')

    // Verify sidebar link is active
    const sidebarLink = page.locator('.nav-link--active', { hasText: 'Habits' })
    await expect(sidebarLink).toBeVisible()
  })
})
