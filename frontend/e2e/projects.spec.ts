import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

/** Helper: create a project via the add modal */
async function createProject(page: import('@playwright/test').Page, name: string) {
  await page.getByTestId('project-add-button').click()
  await expect(page.getByTestId('project-name-input')).toBeVisible({ timeout: 5000 })
  await page.getByTestId('project-name-input').fill(name)
  await page.getByTestId('project-submit-button').click()
  await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
  await expect(page.getByTestId('project-name-input')).not.toBeVisible({ timeout: 3000 })
}

/** Helper: select a project by clicking its row */
async function selectProject(page: import('@playwright/test').Page, name: string) {
  const project = page.getByTestId('project-item').filter({ hasText: name })
  await project.click()
  await expect(page.locator('.projects-page__items-header')).toContainText(name, { timeout: 5000 })
}

/** Helper: create an item in the currently selected project */
async function createItem(page: import('@playwright/test').Page, title: string, notes = '') {
  await page.getByTestId('project-item-add-button').click()
  await expect(page.getByTestId('project-item-title-input')).toBeVisible({ timeout: 5000 })
  await page.getByTestId('project-item-title-input').fill(title)
  if (notes) {
    await page.getByTestId('project-item-notes-input').fill(notes)
  }
  await page.getByTestId('project-item-submit-button').click()
  await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
  await expect(page.getByTestId('project-item-title-input')).not.toBeVisible({ timeout: 3000 })
}

// Smoke tests only — interaction-heavy tests (edit, search, deps modal,
// membership modal, archive, complete) are covered by component integration
// tests in src/views/__tests__/ProjectsView.test.ts

test.describe('Projects Page', () => {
  test('API calls succeed through Traefik routing (CORS check)', async ({ page }) => {
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/projects')
    await expect(page.locator('.projects-page')).toBeVisible({ timeout: 10000 })
    await expect(page.locator(ERROR)).not.toBeVisible()
    expect(apiErrors).toEqual([])
  })

  test('loads the page with correct title', async ({ page }) => {
    await page.goto('/projects')
    await expect(page).toHaveTitle('Projects | iChrisBirch')
  })

  test('creates a new project and verifies it appears', async ({ page }) => {
    await page.goto('/projects')

    const name = `E2E Project ${Date.now()}`
    await createProject(page, name)
    await expect(page.getByTestId('project-item').filter({ hasText: name })).toBeVisible()
  })

  test('creates an item in a project', async ({ page }) => {
    await page.goto('/projects')

    const projName = `E2E Items ${Date.now()}`
    const itemTitle = `E2E Item ${Date.now()}`
    await createProject(page, projName)
    await selectProject(page, projName)
    await createItem(page, itemTitle, 'Some notes')

    await expect(page.getByTestId('project-item-row').filter({ hasText: itemTitle })).toBeVisible()
  })

  test('deletes a project and verifies it is removed', async ({ page }) => {
    await page.goto('/projects')

    const name = `E2E DelProj ${Date.now()}`
    await createProject(page, name)
    await selectProject(page, name)

    await page.getByTestId('project-delete-button').click()

    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
    await expect(page.getByTestId('project-item').filter({ hasText: name })).not.toBeVisible()
  })

  test('sidebar navigation to projects works', async ({ page }) => {
    await page.goto('/projects')
    await expect(page).toHaveTitle('Projects | iChrisBirch')

    const sidebarLink = page.locator('.nav-link--active', { hasText: 'Projects' })
    await expect(sidebarLink).toBeVisible()
  })
})
