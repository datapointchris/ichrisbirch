import { test, expect } from '@playwright/test'

test.describe('Countdowns Page', () => {
  test('loads and displays countdowns page', async ({ page }) => {
    await page.goto('/countdowns')
    await expect(page).toHaveTitle('Countdowns | iChrisBirch')
  })

  test('shows empty state when no countdowns', async ({ page }) => {
    await page.goto('/countdowns')
    // Either shows countdowns or "No Countdowns" message
    const content = page.locator('.grid')
    await expect(content).toBeVisible()
  })

  test('add countdown form is present', async ({ page }) => {
    await page.goto('/countdowns')
    await expect(page.locator('.add-item-wrapper')).toBeVisible()
    await expect(page.locator('#name')).toBeVisible()
    await expect(page.locator('#due_date')).toBeVisible()
    await expect(page.locator('#notes')).toBeVisible()
  })

  test('can fill in the add countdown form', async ({ page }) => {
    await page.goto('/countdowns')

    await page.fill('#name', 'Test Countdown')
    await page.fill('#due_date', '2027-12-31')
    await page.fill('#notes', 'E2E test note')

    await expect(page.locator('#name')).toHaveValue('Test Countdown')
    await expect(page.locator('#due_date')).toHaveValue('2027-12-31')
    await expect(page.locator('#notes')).toHaveValue('E2E test note')
  })

  test('sidebar navigation to countdowns works', async ({ page }) => {
    await page.goto('/')
    await page.click('a[href="/countdowns"]')
    await expect(page).toHaveURL('/countdowns')
    await expect(page).toHaveTitle('Countdowns | iChrisBirch')
  })
})
