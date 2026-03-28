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
  // Wait for the items pane header to show the project name
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

/** Helper: create a project, select it, and add items */
async function setupProjectWithItems(
  page: import('@playwright/test').Page,
  projectName: string,
  itemTitles: string[],
) {
  await createProject(page, projectName)
  await selectProject(page, projectName)
  for (const title of itemTitles) {
    await createItem(page, title)
  }
}

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

  test('creates a new project and verifies it appears in the sidebar', async ({ page }) => {
    await page.goto('/projects')

    const name = `E2E Project ${Date.now()}`
    await createProject(page, name)
    await expect(page.getByTestId('project-item').filter({ hasText: name })).toBeVisible()
  })

  test('selects a project and shows items pane', async ({ page }) => {
    await page.goto('/projects')

    const name = `E2E Select ${Date.now()}`
    await createProject(page, name)
    await selectProject(page, name)

    // Items pane should show the project name and add button
    await expect(page.getByTestId('project-item-add-button')).toBeVisible()
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

  test('deletes an item and verifies it is removed', async ({ page }) => {
    await page.goto('/projects')

    const projName = `E2E DelItem ${Date.now()}`
    const itemTitle = `E2E Delete Me ${Date.now()}`
    await setupProjectWithItems(page, projName, [itemTitle])

    const row = page.getByTestId('project-item-row').filter({ hasText: itemTitle })
    await expect(row).toBeVisible()
    await row.getByTestId('project-item-delete-button').click()

    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
    await expect(row).not.toBeVisible()
  })

  test('completes an item via the check button', async ({ page }) => {
    await page.goto('/projects')

    const projName = `E2E Complete ${Date.now()}`
    const itemTitle = `E2E Check ${Date.now()}`
    await setupProjectWithItems(page, projName, [itemTitle])

    const row = page.getByTestId('project-item-row').filter({ hasText: itemTitle })
    await row.getByTestId('project-item-complete-button').click()

    await expect(page.locator(SUCCESS, { hasText: 'completed' })).toBeVisible({ timeout: 5000 })
    await expect(row).toHaveClass(/projects-page__item--completed/, { timeout: 5000 })
  })

  test('archives an item and verifies visual change', async ({ page }) => {
    await page.goto('/projects')

    const projName = `E2E Archive ${Date.now()}`
    const itemTitle = `E2E Arch ${Date.now()}`
    await setupProjectWithItems(page, projName, [itemTitle])

    const row = page.getByTestId('project-item-row').filter({ hasText: itemTitle })
    await row.getByTestId('project-item-archive-button').click()

    await expect(page.locator(SUCCESS, { hasText: 'archived' })).toBeVisible({ timeout: 5000 })
    await expect(row).toHaveClass(/projects-page__item--archived/, { timeout: 5000 })
  })

  test('edits a project name', async ({ page }) => {
    await page.goto('/projects')

    const name = `E2E EditProj ${Date.now()}`
    const newName = `E2E Renamed ${Date.now()}`
    await createProject(page, name)

    const projectRow = page.getByTestId('project-item').filter({ hasText: name })
    await projectRow.getByTestId('project-edit-button').click()

    await expect(page.getByTestId('project-name-input')).toBeVisible({ timeout: 5000 })
    await page.getByTestId('project-name-input').fill(newName)
    await page.getByTestId('project-submit-button').click()

    await expect(page.locator(SUCCESS, { hasText: 'updated' })).toBeVisible({ timeout: 5000 })
    await expect(page.getByTestId('project-item').filter({ hasText: newName })).toBeVisible()
  })

  test('edits an item title', async ({ page }) => {
    await page.goto('/projects')

    const projName = `E2E EditItem ${Date.now()}`
    const itemTitle = `E2E Original ${Date.now()}`
    const newTitle = `E2E Edited ${Date.now()}`
    await setupProjectWithItems(page, projName, [itemTitle])

    const row = page.getByTestId('project-item-row').filter({ hasText: itemTitle })
    await row.getByTestId('project-item-edit-button').click()

    await expect(page.getByTestId('project-item-title-input')).toBeVisible({ timeout: 5000 })
    await page.getByTestId('project-item-title-input').fill(newTitle)
    await page.getByTestId('project-item-submit-button').click()

    await expect(page.locator(SUCCESS, { hasText: 'updated' })).toBeVisible({ timeout: 5000 })
    await expect(page.getByTestId('project-item-row').filter({ hasText: newTitle })).toBeVisible()
  })

  test('deletes a project and verifies it is removed', async ({ page }) => {
    await page.goto('/projects')

    const name = `E2E DelProj ${Date.now()}`
    await createProject(page, name)

    const projectRow = page.getByTestId('project-item').filter({ hasText: name })
    await expect(projectRow).toBeVisible()
    await projectRow.getByTestId('project-delete-button').click()

    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
    await expect(projectRow).not.toBeVisible()
  })

  test('searches for items across projects', async ({ page }) => {
    await page.goto('/projects')

    const ts = Date.now()
    const projName = `E2E Search ${ts}`
    const itemTitle = `Searchable Widget ${ts}`
    await setupProjectWithItems(page, projName, [itemTitle])

    // Use search
    await page.getByTestId('project-search-input').fill(`Widget ${ts}`)
    await page.getByTestId('project-search-button').click()

    // Should show search results
    await expect(page.getByTestId('project-search-result').filter({ hasText: itemTitle })).toBeVisible({
      timeout: 5000,
    })

    // Clear search returns to normal view
    await page.getByTestId('project-search-clear').click()
    await expect(page.getByTestId('project-search-result')).not.toBeVisible()
  })

  test('opens manage dependencies modal from item row', async ({ page }) => {
    await page.goto('/projects')

    const projName = `E2E Deps ${Date.now()}`
    const items = [`Dep Item A ${Date.now()}`, `Dep Item B ${Date.now()}`]
    await setupProjectWithItems(page, projName, items)

    // Open deps modal on first item
    const row = page.getByTestId('project-item-row').filter({ hasText: items[0] })
    await row.getByTestId('project-item-deps-button').click()

    // Modal should be visible with item title
    await expect(page.locator('.manage-deps')).toBeVisible({ timeout: 5000 })
    await expect(page.locator('.manage-deps__subtitle')).toContainText(items[0]!)

    // Second item should be available to add as dependency
    await expect(page.getByTestId('dependency-add-button')).toBeVisible()
  })

  test('adds and removes a dependency', async ({ page }) => {
    await page.goto('/projects')

    const ts = Date.now()
    const projName = `E2E DepCRUD ${ts}`
    const items = [`Parent ${ts}`, `Blocker ${ts}`]
    await setupProjectWithItems(page, projName, items)

    // Open deps modal on first item
    const row = page.getByTestId('project-item-row').filter({ hasText: items[0] })
    await row.getByTestId('project-item-deps-button').click()
    await expect(page.locator('.manage-deps')).toBeVisible({ timeout: 5000 })

    // Add the second item as a dependency
    const addRow = page.locator('.manage-deps__row').filter({ hasText: items[1] })
    await addRow.getByTestId('dependency-add-button').click()

    // Should now appear in "Blocked by" section with a remove button
    await expect(page.getByTestId('dependency-remove-button')).toBeVisible({ timeout: 5000 })

    // Remove the dependency
    const depRow = page.locator('.manage-deps__row').filter({ hasText: items[1] })
    await depRow.getByTestId('dependency-remove-button').click()

    // Should be back in the "Add dependency" section
    await expect(depRow.getByTestId('dependency-add-button')).toBeVisible({ timeout: 5000 })
  })

  test('opens manage projects modal from item row', async ({ page }) => {
    await page.goto('/projects')

    const ts = Date.now()
    const projName = `E2E MemProj ${ts}`
    const itemTitle = `Membership Item ${ts}`
    await setupProjectWithItems(page, projName, [itemTitle])

    // Open projects modal
    const row = page.getByTestId('project-item-row').filter({ hasText: itemTitle })
    await row.getByTestId('project-item-projects-button').click()

    // Modal should show with the item title and current project membership
    await expect(page.locator('.manage-projects')).toBeVisible({ timeout: 5000 })
    await expect(page.locator('.manage-projects__subtitle')).toContainText(itemTitle)
    // Should show the current project in "Member of"
    await expect(page.locator('.manage-projects__name').first()).toContainText(projName)
  })

  test('adds item to another project via membership modal', async ({ page }) => {
    await page.goto('/projects')

    const ts = Date.now()
    const projA = `E2E ProjA ${ts}`
    const projB = `E2E ProjB ${ts}`
    const itemTitle = `Cross-proj Item ${ts}`

    // Create two projects
    await createProject(page, projA)
    await createProject(page, projB)

    // Add item to first project
    await selectProject(page, projA)
    await createItem(page, itemTitle)

    // Open membership modal
    const row = page.getByTestId('project-item-row').filter({ hasText: itemTitle })
    await row.getByTestId('project-item-projects-button').click()
    await expect(page.locator('.manage-projects')).toBeVisible({ timeout: 5000 })

    // Add to second project
    const addRow = page.locator('.manage-projects__row').filter({ hasText: projB })
    await addRow.getByTestId('membership-add-button').click()

    // Should now appear in "Member of" section with remove button
    await expect(
      page.locator('.manage-projects__row').filter({ hasText: projB }).getByTestId('membership-remove-button'),
    ).toBeVisible({ timeout: 5000 })
  })

  test('sidebar navigation to projects works', async ({ page }) => {
    await page.goto('/projects')
    await expect(page).toHaveTitle('Projects | iChrisBirch')

    const sidebarLink = page.locator('.nav-link--active', { hasText: 'Projects' })
    await expect(sidebarLink).toBeVisible()
  })
})
