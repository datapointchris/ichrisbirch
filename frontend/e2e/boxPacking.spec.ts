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
  await page.getByTestId('box-size-input').click()
  await page.getByTestId(`box-size-input-option-${size}`).click()
  await page.getByTestId('box-name-input').press('Enter')
  await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
}

// Smoke tests only — interaction-heavy tests (edit, search, orphan,
// assign orphan, view modes) are covered by component integration
// tests in src/views/__tests__/BoxPackingView.test.ts

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

  test('creates a new box and verifies it appears', async ({ page }) => {
    await page.goto('/box-packing')

    const ts = Date.now()
    const name = `E2E Box ${ts}`
    await createBox(page, name, String(ts % 100000), 'Small')
    await expect(page.locator(SUCCESS).first()).toContainText('added')

    await expect(page.getByTestId('box-item').filter({ hasText: name })).toBeVisible()
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

  test('adds an item to a box and verifies it appears', async ({ page }) => {
    await page.goto('/box-packing')

    const ts = Date.now()
    const boxName = `E2E ItemBox ${ts}`
    await createBox(page, boxName, String(ts % 100000))

    const boxRow = page.getByTestId('box-item').filter({ hasText: boxName })
    await expect(boxRow).toBeVisible()

    const itemName = `E2E Item ${ts}`
    await page.getByTestId('item-add-button').click()
    await expect(page.getByTestId('item-name-input')).toBeVisible({ timeout: 5000 })
    await page.getByTestId('item-box-input').click()
    await page.locator('.neu-select__option', { hasText: boxName }).click()
    await page.getByTestId('item-name-input').fill(itemName)
    await page.getByTestId('item-name-input').press('Enter')
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })

    await expect(boxRow.getByTestId('box-content-item').filter({ hasText: itemName })).toBeVisible()

    // Clean up
    await boxRow.getByTestId('box-delete-button').click()
    await expect(page.locator(SUCCESS, { hasText: 'deleted' })).toBeVisible({ timeout: 5000 })
  })

  test('sidebar navigation shows box packing as active', async ({ page }) => {
    await page.goto('/box-packing')
    const sidebarLink = page.locator('.nav-link--active', { hasText: 'Box Packing' })
    await expect(sidebarLink).toBeVisible()
  })
})
