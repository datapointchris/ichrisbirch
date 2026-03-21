import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

/** Helper: open the add box modal, fill in fields, and submit */
async function createBox(
  page: import('@playwright/test').Page,
  name: string,
  boxNumber: string,
  size = 'Medium',
) {
  await page.getByTestId('box-add-button').click()
  await expect(page.getByTestId('box-name-input')).toBeVisible({ timeout: 5000 })
  await page.getByTestId('box-name-input').fill(name)
  await page.getByTestId('box-number-input').fill(boxNumber)
  await page.getByTestId('box-size-input').selectOption(size)
  await page.getByTestId('box-name-input').press('Enter')
  await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
}

/** Helper: add an item to a box via the "Add Item to Box" button inside the expanded box */
async function createItemInBox(
  page: import('@playwright/test').Page,
  boxRow: import('@playwright/test').Locator,
  itemName: string,
) {
  await boxRow.getByTestId('box-add-item-button').click()
  await expect(page.getByTestId('item-name-input')).toBeVisible({ timeout: 5000 })
  await page.getByTestId('item-name-input').fill(itemName)
  await page.getByTestId('item-name-input').press('Enter')
  await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
}

test.describe('Box Packing Page', () => {
  test('API calls succeed through Traefik routing (CORS check)', async ({ page }) => {
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/box-packing')
    await expect(page.locator('.box-controls').first()).toBeVisible({ timeout: 10000 })
    await expect(page.locator(ERROR)).not.toBeVisible()
    expect(apiErrors).toEqual([])
  })

  test('loads the page with correct title', async ({ page }) => {
    await page.goto('/box-packing')
    await expect(page).toHaveTitle('Box Packing | iChrisBirch')
  })

  test('add box button opens modal with all fields', async ({ page }) => {
    await page.goto('/box-packing')

    await page.getByTestId('box-add-button').click()
    await expect(page.getByTestId('box-name-input')).toBeVisible({ timeout: 5000 })
    await expect(page.getByTestId('box-number-input')).toBeVisible()
    await expect(page.getByTestId('box-size-input')).toBeVisible()
    await page.getByTestId('box-cancel-button').click()
  })

  test('creates a new box and verifies it appears', async ({ page }) => {
    await page.goto('/box-packing')

    const ts = Date.now()
    const name = `E2E Box ${ts}`
    await createBox(page, name, String(ts % 100000), 'Small')
    await expect(page.locator(SUCCESS).first()).toContainText('added')

    await expect(page.getByTestId('box-item').filter({ hasText: name })).toBeVisible()
  })

  test('edits a box via the modal', async ({ page }) => {
    await page.goto('/box-packing')

    const ts = Date.now()
    const name = `E2E EditBox ${ts}`
    await createBox(page, name, String(ts % 100000))

    const boxRow = page.getByTestId('box-item').filter({ hasText: name })
    await expect(boxRow).toBeVisible()
    await boxRow.getByTestId('box-edit-button').click()

    await expect(page.getByTestId('box-name-input')).toBeVisible({ timeout: 5000 })
    await expect(page.getByTestId('box-name-input')).toHaveValue(name)

    const updatedName = `${name} Updated`
    await page.getByTestId('box-name-input').fill(updatedName)
    await page.getByTestId('box-name-input').press('Enter')

    await expect(page.locator(SUCCESS, { hasText: 'updated' })).toBeVisible({ timeout: 5000 })
    await expect(page.getByTestId('box-item').filter({ hasText: updatedName })).toBeVisible()

    // Clean up
    const updatedBox = page.getByTestId('box-item').filter({ hasText: updatedName })
    await updatedBox.getByTestId('box-delete-button').click()
    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
  })

  test('deletes a box', async ({ page }) => {
    await page.goto('/box-packing')

    const ts = Date.now()
    const name = `E2E DeleteBox ${ts}`
    await createBox(page, name, String(ts % 100000))

    const boxRow = page.getByTestId('box-item').filter({ hasText: name })
    await expect(boxRow).toBeVisible()
    await boxRow.getByTestId('box-delete-button').click()

    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
    await expect(boxRow).not.toBeVisible()
  })

  test('block view shows items and add-item button without expand', async ({ page }) => {
    await page.goto('/box-packing')

    const ts = Date.now()
    const name = `E2E BlockBox ${ts}`
    await createBox(page, name, String(ts % 100000))

    const boxRow = page.getByTestId('box-item').filter({ hasText: name })
    // In block view, items section is always visible
    await expect(boxRow.getByTestId('box-add-item-button')).toBeVisible()

    // Clean up
    await boxRow.getByTestId('box-delete-button').click()
    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
  })

  test('search finds items across boxes', async ({ page }) => {
    await page.goto('/box-packing')

    await page.getByTestId('box-search-input').fill('nonexistent-item-query-12345')
    await page.getByTestId('box-search-button').click()

    // Should show no results or results
    await expect(page.getByText('No results')).toBeVisible({ timeout: 5000 })

    // Clear returns to box list
    await page.getByTestId('box-search-clear-button').click()
    await expect(page.locator('.box-controls').first()).toBeVisible()
  })

  test('adds an item to a box and verifies it appears', async ({ page }) => {
    await page.goto('/box-packing')

    const ts = Date.now()
    const boxName = `E2E ItemBox ${ts}`
    await createBox(page, boxName, String(ts % 100000))

    const boxRow = page.getByTestId('box-item').filter({ hasText: boxName })
    await expect(boxRow).toBeVisible()

    // Add item via the top-level "Add Item" button (tests box dropdown selection)
    const itemName = `E2E Item ${ts}`
    await page.getByTestId('item-add-button').click()
    await expect(page.getByTestId('item-name-input')).toBeVisible({ timeout: 5000 })
    // Find the option that contains our box name and select it by its value
    const boxOption = page.getByTestId('item-box-input').locator('option', { hasText: boxName })
    const boxValue = await boxOption.getAttribute('value')
    await page.getByTestId('item-box-input').selectOption(boxValue!)
    await page.getByTestId('item-name-input').fill(itemName)
    await page.getByTestId('item-name-input').press('Enter')
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })

    // Verify item appears inside the box
    await expect(boxRow.getByTestId('box-content-item').filter({ hasText: itemName })).toBeVisible()

    // Clean up
    await boxRow.getByTestId('box-delete-button').click()
    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
  })

  test('orphans an item from a box', async ({ page }) => {
    await page.goto('/box-packing')

    const ts = Date.now()
    const boxName = `E2E OrphanBox ${ts}`
    await createBox(page, boxName, String(ts % 100000))

    // Add an item
    const boxRow = page.getByTestId('box-item').filter({ hasText: boxName })
    const itemName = `E2E Orphan ${ts}`
    await createItemInBox(page, boxRow, itemName)

    // Orphan the item
    const itemRow = boxRow.getByTestId('box-content-item').filter({ hasText: itemName })
    await itemRow.getByTestId('item-orphan-button').click()
    await expect(page.locator(SUCCESS, { hasText: 'removed' })).toBeVisible({ timeout: 5000 })

    // Item should no longer be in the box
    await expect(itemRow).not.toBeVisible()

    // Orphans button should show count
    await expect(page.getByTestId('orphans-button')).toContainText('Orphans')

    // Clean up — delete box and orphan via orphans modal
    await boxRow.getByTestId('box-delete-button').click()
    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
    await page.getByTestId('orphans-button').click()
    await expect(page.getByTestId('orphan-item').filter({ hasText: itemName })).toBeVisible({ timeout: 5000 })
    await page.getByTestId('orphan-item').filter({ hasText: itemName }).getByTestId('orphan-delete-button').click()
    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
  })

  test('assigns an orphan to a box via the orphans modal', async ({ page }) => {
    await page.goto('/box-packing')

    const ts = Date.now()
    const boxName = `E2E AssignBox ${ts}`
    const boxNumber = String(ts % 100000)
    await createBox(page, boxName, boxNumber)

    // Add an item then orphan it
    const boxRow = page.getByTestId('box-item').filter({ hasText: boxName })
    const itemName = `E2E Assign ${ts}`
    await createItemInBox(page, boxRow, itemName)

    const itemRow = boxRow.getByTestId('box-content-item').filter({ hasText: itemName })
    await itemRow.getByTestId('item-orphan-button').click()
    await expect(page.locator(SUCCESS, { hasText: 'removed' })).toBeVisible({ timeout: 5000 })

    // Open orphans modal and assign back to the box
    await page.getByTestId('orphans-button').click()
    const orphanRow = page.getByTestId('orphan-item').filter({ hasText: itemName })
    await expect(orphanRow).toBeVisible({ timeout: 5000 })

    // Click the NeuSelect trigger to open the box dropdown
    const assignSelect = orphanRow.locator('.neu-select__trigger')
    await assignSelect.click()

    // Select the box from the dropdown (teleported to body)
    // Use dispatchEvent since the fixed-position dropdown may be outside viewport
    const boxOption = page.locator('.neu-select__option', { hasText: boxName })
    await expect(boxOption).toBeVisible({ timeout: 5000 })
    await boxOption.dispatchEvent('click')
    await expect(page.locator(SUCCESS, { hasText: 'assigned' })).toBeVisible({ timeout: 5000 })

    // Orphan should be gone from the modal
    await expect(orphanRow).not.toBeVisible()

    // Close the orphans modal
    await page.getByTestId('orphans-close-button').click()
    await expect(page.getByTestId('listing-modal')).not.toBeVisible({ timeout: 5000 })
    await boxRow.getByTestId('box-delete-button').click()
    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
  })

  test('sidebar navigation shows box packing as active', async ({ page }) => {
    await page.goto('/box-packing')
    const sidebarLink = page.locator('.nav-link--active', { hasText: 'Box Packing' })
    await expect(sidebarLink).toBeVisible()
  })
})
