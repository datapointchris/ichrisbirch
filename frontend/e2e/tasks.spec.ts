import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

/** Helper: open the add task modal, fill in fields, and submit */
async function createTask(page: import('@playwright/test').Page, name: string, priority = '15') {
  await page.getByTestId('task-add-button').click()
  await expect(page.getByTestId('add-edit-modal')).toBeVisible({ timeout: 5000 })
  await page.getByTestId('task-name-input').fill(name)
  await page.getByTestId('task-category-tile-Chore').click()
  await page.getByTestId('task-priority-input').fill(priority)
  await page.getByTestId('task-priority-input').press('Enter')
  await expect(page.getByTestId('add-edit-modal')).not.toBeVisible({ timeout: 5000 })
  await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
}

// Smoke tests only — interaction-heavy tests (complete, delete, extend,
// search) are covered by component integration tests in
// src/views/__tests__/TasksView.test.ts

test.describe('Tasks Page', () => {
  test('API calls succeed through Traefik routing (CORS check)', async ({ page }) => {
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/tasks')
    await expect(page.getByTestId('task-info-bar')).toBeVisible({ timeout: 10000 })
    await expect(page.locator(ERROR)).not.toBeVisible()
    expect(apiErrors).toEqual([])
  })

  test('loads the page and displays the title', async ({ page }) => {
    await page.goto('/tasks')
    await expect(page).toHaveTitle('Priority Tasks | iChrisBirch')
    await expect(page.getByTestId('task-info-bar')).toBeVisible()
  })

  test('navigates to outstanding tasks page', async ({ page }) => {
    await page.goto('/tasks/todo')
    await expect(page.getByTestId('task-info-bar')).toBeVisible({ timeout: 10000 })
  })

  test('navigates to completed tasks page', async ({ page }) => {
    await page.goto('/tasks/completed')
    await expect(page).toHaveTitle('Completed Tasks | iChrisBirch')
  })

  test('opens add task modal and creates a task', async ({ page }) => {
    await page.goto('/tasks')
    await expect(page.getByTestId('task-info-bar')).toBeVisible({ timeout: 10000 })

    const taskName = `E2E Task ${Date.now()}`
    await createTask(page, taskName)

    await page.goto('/tasks/todo')
    await expect(page.getByTestId('task-item').filter({ hasText: taskName })).toBeVisible({ timeout: 10000 })
  })

  test('sidebar navigation to tasks works', async ({ page }) => {
    await page.goto('/tasks')
    await expect(page).toHaveTitle('Priority Tasks | iChrisBirch')

    const sidebarLink = page.locator('.nav-link--active', { hasText: 'Tasks' })
    await expect(sidebarLink).toBeVisible()
  })
})
