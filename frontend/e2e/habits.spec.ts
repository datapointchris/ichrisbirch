import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

/** Helper: open the add category modal, fill in name, and submit */
async function createCategory(page: import('@playwright/test').Page, name: string) {
  await page.getByTestId('category-add-button').click()
  await expect(page.getByTestId('category-name-input')).toBeVisible({ timeout: 5000 })
  await page.getByTestId('category-name-input').fill(name)
  await page.getByTestId('category-name-input').press('Enter')
  await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
}

/** Helper: open the add habit modal, fill in name and category, and submit */
async function createHabit(page: import('@playwright/test').Page, name: string, categoryName: string) {
  await page.getByTestId('habit-add-button').click()
  await expect(page.getByTestId('habit-name-input')).toBeVisible({ timeout: 5000 })
  await page.getByTestId('habit-name-input').fill(name)
  await page.getByTestId('habit-category-input').selectOption({ label: categoryName })
  await page.getByTestId('habit-name-input').press('Enter')
  await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
}

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

    await expect(page.locator('a', { hasText: 'Daily Habits' })).toBeVisible()
    await expect(page.locator('a', { hasText: 'Completed' })).toBeVisible()
    await expect(page.locator('a', { hasText: 'Manage' })).toBeVisible()

    await expect(page.locator(ERROR)).not.toBeVisible()
    expect(apiErrors).toEqual([])
  })

  test('Manage page: add buttons open modals', async ({ page }) => {
    await page.goto('/habits/manage')
    await expect(page.locator('h3', { hasText: 'Current Categories' })).toBeVisible({ timeout: 10000 })

    // Habit add button opens modal
    await page.getByTestId('habit-add-button').click()
    await expect(page.getByTestId('habit-name-input')).toBeVisible({ timeout: 5000 })
    await expect(page.getByTestId('habit-category-input')).toBeVisible()
    await page.getByTestId('habit-cancel-button').click()

    // Wait for modal to close
    await expect(page.getByTestId('habit-name-input')).not.toBeVisible({ timeout: 5000 })

    // Category add button opens modal
    await page.getByTestId('category-add-button').click()
    await expect(page.getByTestId('category-name-input')).toBeVisible({ timeout: 5000 })
    await page.getByTestId('category-cancel-button').click()
  })

  test('Manage page: create category then create habit', async ({ page }) => {
    await page.goto('/habits/manage')
    await expect(page.locator('h3', { hasText: 'Current Categories' })).toBeVisible({ timeout: 10000 })

    const catName = `E2E Cat ${Date.now()}`
    await createCategory(page, catName)
    await expect(page.locator(SUCCESS).first()).toContainText('added')

    const habitName = `E2E Habit ${Date.now()}`
    await createHabit(page, habitName, catName)

    await expect(page.getByTestId('habit-item').filter({ hasText: habitName })).toBeVisible()
  })

  test('Manage page: edit a habit via the modal', async ({ page }) => {
    await page.goto('/habits/manage')
    await expect(page.locator('h3', { hasText: 'Current Categories' })).toBeVisible({ timeout: 10000 })

    const catName = `E2E EditCat ${Date.now()}`
    await createCategory(page, catName)

    const habitName = `E2E EditHabit ${Date.now()}`
    await createHabit(page, habitName, catName)

    const habitRow = page.getByTestId('habit-item').filter({ hasText: habitName })
    await expect(habitRow).toBeVisible()
    await habitRow.getByTestId('habit-edit-button').click()

    await expect(page.getByTestId('habit-name-input')).toBeVisible({ timeout: 5000 })
    await expect(page.getByTestId('habit-name-input')).toHaveValue(habitName)

    const updatedName = `${habitName} Updated`
    await page.getByTestId('habit-name-input').fill(updatedName)
    await page.getByTestId('habit-name-input').press('Enter')

    await expect(page.locator(SUCCESS, { hasText: 'updated' })).toBeVisible({ timeout: 5000 })
    await expect(page.getByTestId('habit-item').filter({ hasText: updatedName })).toBeVisible()
  })

  test('Daily page: complete a habit moves it to done', async ({ page }) => {
    await page.goto('/habits')

    const todoColumn = page.locator('.habits__column').first()
    await expect(todoColumn).toBeVisible({ timeout: 10000 })

    const firstCheck = page.locator('.habits__check').first()
    if (await firstCheck.isVisible({ timeout: 3000 }).catch(() => false)) {
      const habitName = await page.locator('.habits__item-name').first().textContent()
      await firstCheck.click()
      await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })

      if (habitName) {
        await expect(page.locator('.habits__item--done', { hasText: habitName })).toBeVisible({
          timeout: 5000,
        })
      }
    }
  })

  test('Manage page: hibernate and revive a habit', async ({ page }) => {
    await page.goto('/habits/manage')
    await expect(page.locator('h3', { hasText: 'Current Habits' })).toBeVisible({ timeout: 10000 })

    const catName = `E2E HibCat ${Date.now()}`
    await createCategory(page, catName)

    const habitName = `E2E HibHabit ${Date.now()}`
    await createHabit(page, habitName, catName)

    const currentRow = page.getByTestId('habit-item').filter({ hasText: habitName })
    await expect(currentRow).toBeVisible()

    // Hibernate it
    await currentRow.getByTestId('habit-hibernate-button').click()
    await expect(page.locator(SUCCESS, { hasText: 'hibernated' })).toBeVisible({ timeout: 5000 })

    // Should now be in Hibernating section
    await expect(page.getByTestId('habit-item-hibernating').filter({ hasText: habitName })).toBeVisible()

    // Revive it
    const hibernatedRow = page.getByTestId('habit-item-hibernating').filter({ hasText: habitName })
    await hibernatedRow.getByTestId('habit-revive-button').click()
    await expect(page.locator(SUCCESS, { hasText: 'revived' })).toBeVisible({ timeout: 5000 })

    // Should be back in Current Habits
    await expect(page.getByTestId('habit-item').filter({ hasText: habitName })).toBeVisible()
  })

  test('Completed page: filter and chart renders', async ({ page }) => {
    await page.goto('/habits/completed')
    await expect(page).toHaveTitle('Completed Habits | iChrisBirch')

    await expect(page.locator('label', { hasText: 'This Week' })).toBeVisible({ timeout: 10000 })
    await expect(page.locator('label', { hasText: 'Last 30' })).toBeVisible()

    await page.locator('label', { hasText: 'All' }).click()
    await page.locator('button', { hasText: 'Filter' }).click()

    const chartOrEmpty = page.locator('canvas, .habits-completed__count--empty')
    await expect(chartOrEmpty.first()).toBeVisible({ timeout: 10000 })
  })

  test('Subnav navigation between sub-pages works', async ({ page }) => {
    await page.goto('/habits')
    await expect(page).toHaveTitle('Daily Habits | iChrisBirch')

    await page.locator('a', { hasText: 'Completed' }).click()
    await expect(page).toHaveTitle('Completed Habits | iChrisBirch')

    await page.locator('a', { hasText: 'Manage' }).click()
    await expect(page).toHaveTitle('Manage Habits | iChrisBirch')

    await page.locator('a', { hasText: 'Daily Habits' }).click()
    await expect(page).toHaveTitle('Daily Habits | iChrisBirch')
  })

  test('sidebar navigation to habits works', async ({ page }) => {
    await page.goto('/habits')
    await expect(page).toHaveTitle('Daily Habits | iChrisBirch')

    const sidebarLink = page.locator('.nav-link--active', { hasText: 'Habits' })
    await expect(sidebarLink).toBeVisible()
  })
})
