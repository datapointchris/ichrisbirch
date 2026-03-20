import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

test.describe('Tasks Page', () => {
  test('API calls succeed through Traefik routing (CORS check)', async ({ page }) => {
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/tasks')

    // Wait for the task info bar — means the API GET for tasks succeeded
    await expect(page.locator('.task-layout__info')).toBeVisible({ timeout: 10000 })

    await expect(page.locator(ERROR)).not.toBeVisible()
    expect(apiErrors).toEqual([])
  })

  test('loads the page and displays the title', async ({ page }) => {
    await page.goto('/tasks')
    await expect(page).toHaveTitle('Priority Tasks | iChrisBirch')
    await expect(page.locator('.task-layout__info')).toBeVisible()
  })

  test('subnav links are visible', async ({ page }) => {
    await page.goto('/tasks')
    await expect(page.locator('.tasks-subnav__link', { hasText: 'Priority Tasks' })).toBeVisible()
    await expect(page.locator('.tasks-subnav__link', { hasText: 'Outstanding Tasks' })).toBeVisible()
    await expect(page.locator('.tasks-subnav__link', { hasText: 'Completed Tasks' })).toBeVisible()
  })

  test('priority page shows Priority Tasks heading', async ({ page }) => {
    await page.goto('/tasks')
    await expect(page.locator('.task-layout__info')).toBeVisible({ timeout: 10000 })
    await expect(page.locator('.task-layout__title', { hasText: 'Priority Tasks' })).toBeVisible()
  })

  test('navigates to outstanding tasks page', async ({ page }) => {
    await page.goto('/tasks/todo')
    await expect(page.locator('.task-layout__info')).toBeVisible({ timeout: 10000 })
    await expect(page.locator('.task-layout__title', { hasText: 'Outstanding Tasks' })).toBeVisible()
  })

  test('navigates to completed tasks page', async ({ page }) => {
    await page.goto('/tasks/completed')
    await expect(page.locator('.task-layout__title', { hasText: 'Completed Tasks' })).toBeVisible({
      timeout: 10000,
    })
  })

  test('opens add task modal and creates a task', async ({ page }) => {
    await page.goto('/tasks')
    await expect(page.locator('.task-layout__info')).toBeVisible({ timeout: 10000 })

    const taskName = `E2E Task ${Date.now()}`

    // Click the "Add Task" button in the subnav
    await page.locator('.tasks-subnav .button', { hasText: 'Add Task' }).click()

    // Wait for the modal to animate in
    await expect(page.locator('#add-task-window.visible')).toBeVisible({ timeout: 5000 })

    // Fill in the form
    await page.fill('#add-task-name', taskName)
    await page.locator('.add-task-categories__tile', { hasText: 'Chore' }).click()
    await page.fill('#add-task-priority', '15')

    // Submit via form submission (button can be off-viewport in small viewports)
    await page.locator('#add-task-priority').press('Enter')

    // Wait for the success animation to complete and modal to close
    await expect(page.locator('#add-task-window.visible')).not.toBeVisible({ timeout: 5000 })

    // Verify success notification
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })

    // Navigate to outstanding tasks to find our created task
    await page.goto('/tasks/todo')
    await expect(page.locator('.task-layout__title', { hasText: 'Outstanding Tasks' })).toBeVisible({
      timeout: 10000,
    })
    await expect(page.locator('.task', { hasText: taskName })).toBeVisible()
  })

  test('completes a task from the todo page', async ({ page }) => {
    await page.goto('/tasks')
    await expect(page.locator('.task-layout__info')).toBeVisible({ timeout: 10000 })

    // Create a task to complete
    const taskName = `E2E Complete ${Date.now()}`
    await page.locator('.tasks-subnav .button', { hasText: 'Add Task' }).click()
    await expect(page.locator('#add-task-window.visible')).toBeVisible({ timeout: 5000 })
    await page.fill('#add-task-name', taskName)
    await page.locator('.add-task-categories__tile', { hasText: 'Chore' }).click()
    await page.fill('#add-task-priority', '20')
    await page.locator('#add-task-priority').press('Enter')
    await expect(page.locator('#add-task-window.visible')).not.toBeVisible({ timeout: 5000 })
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })

    // Navigate to todo to find it
    await page.goto('/tasks/todo')
    await expect(page.locator('.task-layout__title', { hasText: 'Outstanding Tasks' })).toBeVisible({
      timeout: 10000,
    })

    // Find the task and click Complete
    const taskCard = page.locator('.task', { hasText: taskName })
    await expect(taskCard).toBeVisible()
    await taskCard.locator('.button', { hasText: 'Complete Task' }).click()

    // Verify it's removed from the todo list
    await expect(taskCard).not.toBeVisible({ timeout: 5000 })

    // Verify success notification
    await expect(page.locator(SUCCESS, { hasText: 'completed' })).toBeVisible({ timeout: 5000 })
  })

  test('deletes a task from the todo page', async ({ page }) => {
    await page.goto('/tasks')
    await expect(page.locator('.task-layout__info')).toBeVisible({ timeout: 10000 })

    // Create a task to delete
    const taskName = `E2E Delete ${Date.now()}`
    await page.locator('.tasks-subnav .button', { hasText: 'Add Task' }).click()
    await expect(page.locator('#add-task-window.visible')).toBeVisible({ timeout: 5000 })
    await page.fill('#add-task-name', taskName)
    await page.locator('.add-task-categories__tile', { hasText: 'Chore' }).click()
    await page.fill('#add-task-priority', '20')
    await page.locator('#add-task-priority').press('Enter')
    await expect(page.locator('#add-task-window.visible')).not.toBeVisible({ timeout: 5000 })
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })

    // Navigate to todo to find it
    await page.goto('/tasks/todo')
    await expect(page.locator('.task-layout__title', { hasText: 'Outstanding Tasks' })).toBeVisible({
      timeout: 10000,
    })

    // Find the task and click Delete
    const taskCard = page.locator('.task', { hasText: taskName })
    await expect(taskCard).toBeVisible()
    await taskCard.locator('.button--danger').click()

    // Verify it's removed
    await expect(taskCard).not.toBeVisible({ timeout: 5000 })

    // Verify success notification
    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
  })

  test('search finds tasks by name', async ({ page }) => {
    await page.goto('/tasks')
    await expect(page.locator('.task-layout__info')).toBeVisible({ timeout: 10000 })

    // Create a task with a unique name to search for
    const searchTag = `srch${Date.now()}`
    const taskName = `E2E ${searchTag}`
    await page.locator('.tasks-subnav .button', { hasText: 'Add Task' }).click()
    await expect(page.locator('#add-task-window.visible')).toBeVisible({ timeout: 5000 })
    await page.fill('#add-task-name', taskName)
    await page.locator('.add-task-categories__tile', { hasText: 'Chore' }).click()
    await page.fill('#add-task-priority', '20')
    await page.locator('#add-task-priority').press('Enter')
    await expect(page.locator('#add-task-window.visible')).not.toBeVisible({ timeout: 5000 })
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })

    // Search for it
    await page.fill('.task-search-form .textbox', searchTag)
    await page.locator('.task-search-form .button').click()

    // Verify search results page shows our task
    await expect(page.locator('.task-layout__title', { hasText: 'Search Results' })).toBeVisible({
      timeout: 10000,
    })
    await expect(page.locator('.task', { hasText: taskName })).toBeVisible()
  })

  test('sidebar navigation to tasks works', async ({ page }) => {
    await page.goto('/tasks')
    await expect(page).toHaveTitle('Priority Tasks | iChrisBirch')

    const sidebarLink = page.locator('.nav-link--active', { hasText: 'Tasks' })
    await expect(sidebarLink).toBeVisible()
  })
})
