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

    // Navigate to outstanding tasks to find it
    await page.goto('/tasks/todo')
    await expect(page.getByTestId('task-item').filter({ hasText: taskName })).toBeVisible({ timeout: 10000 })
  })

  test('completes a task from the todo page', async ({ page }) => {
    await page.goto('/tasks')
    await expect(page.getByTestId('task-info-bar')).toBeVisible({ timeout: 10000 })

    const taskName = `E2E Complete ${Date.now()}`
    await createTask(page, taskName, '20')

    await page.goto('/tasks/todo')
    const taskCard = page.getByTestId('task-item').filter({ hasText: taskName })
    await expect(taskCard).toBeVisible({ timeout: 10000 })
    await taskCard.getByTestId('task-complete-button').click()

    await expect(taskCard).not.toBeVisible({ timeout: 5000 })
    await expect(page.locator(SUCCESS, { hasText: 'completed' })).toBeVisible({ timeout: 5000 })
  })

  test('deletes a task from the todo page', async ({ page }) => {
    await page.goto('/tasks')
    await expect(page.getByTestId('task-info-bar')).toBeVisible({ timeout: 10000 })

    const taskName = `E2E Delete ${Date.now()}`
    await createTask(page, taskName, '20')

    await page.goto('/tasks/todo')
    const taskCard = page.getByTestId('task-item').filter({ hasText: taskName })
    await expect(taskCard).toBeVisible({ timeout: 10000 })
    await taskCard.getByTestId('task-delete-button').click()

    await expect(taskCard).not.toBeVisible({ timeout: 5000 })
    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
  })

  test('extends a task and verifies it remains on the page', async ({ page }) => {
    await page.goto('/tasks')
    await expect(page.getByTestId('task-info-bar')).toBeVisible({ timeout: 10000 })

    const taskName = `E2E Extend ${Date.now()}`
    await createTask(page, taskName, '10')

    await page.goto('/tasks/todo')
    const taskCard = page.getByTestId('task-item').filter({ hasText: taskName })
    await expect(taskCard).toBeVisible({ timeout: 10000 })

    await taskCard.getByTestId('task-extend-7-button').click()
    await expect(page.locator(SUCCESS, { hasText: 'extended' })).toBeVisible({ timeout: 5000 })
    await expect(taskCard).toBeVisible()

    await taskCard.getByTestId('task-extend-30-button').click()
    await expect(page.locator(SUCCESS, { hasText: 'extended' })).toBeVisible({ timeout: 5000 })
    await expect(taskCard).toBeVisible()
  })

  test('search finds tasks by name', async ({ page }) => {
    await page.goto('/tasks')
    await expect(page.getByTestId('task-info-bar')).toBeVisible({ timeout: 10000 })

    const searchTag = `srch${Date.now()}`
    const taskName = `E2E ${searchTag}`
    await createTask(page, taskName, '20')

    await page.getByTestId('task-search-input').fill(searchTag)
    await page.getByTestId('task-search-button').click()

    await expect(page.getByTestId('task-item').filter({ hasText: taskName })).toBeVisible({ timeout: 10000 })
  })

  test('sidebar navigation to tasks works', async ({ page }) => {
    await page.goto('/tasks')
    await expect(page).toHaveTitle('Priority Tasks | iChrisBirch')

    const sidebarLink = page.locator('.nav-link--active', { hasText: 'Tasks' })
    await expect(sidebarLink).toBeVisible()
  })
})
