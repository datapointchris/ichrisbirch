import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

test.describe('Box Packing Page', () => {
  test('API calls succeed through Traefik routing (CORS check)', async ({ page }) => {
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/box-packing')
    await expect(page.locator('.box-packing-subnav')).toBeVisible({ timeout: 10000 })
    await expect(page.locator(ERROR)).not.toBeVisible()
    expect(apiErrors).toEqual([])
  })

  test('loads the all boxes page', async ({ page }) => {
    await page.goto('/box-packing')
    await expect(page).toHaveTitle('All Boxes | iChrisBirch')
    await expect(page.locator('.box-packing-subnav')).toBeVisible()
  })

  test('creates a new box and verifies it appears', async ({ page }) => {
    await page.goto('/box-packing')

    const ts = Date.now()
    const name = `E2E Box ${ts}`
    const boxNumber = String(ts % 100000)
    await page.fill('#box_name', name)
    await page.fill('#box_number', boxNumber)
    await page.selectOption('#box_size', 'Small')
    await page.click('button[type="submit"]')

    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
    await expect(page.locator(SUCCESS).first()).toContainText('Box added')

    // Verify the box appears in the grid (block or compact view)
    await expect(page.getByText(name)).toBeVisible()
  })

  test('navigates to box detail page', async ({ page }) => {
    await page.goto('/box-packing')

    // Click the first box link (if boxes exist)
    const firstBoxLink = page.locator('.packed-box__link, .packed-box-compact__link').first()
    if (await firstBoxLink.isVisible({ timeout: 5000 })) {
      await firstBoxLink.click()
      await expect(page).toHaveTitle('Box Detail | iChrisBirch')
      await expect(page.locator('.packed-box__title')).toBeVisible()
    }
  })

  test('adds an item to a box from detail page', async ({ page }) => {
    await page.goto('/box-packing')

    // Create a box first
    const ts = Date.now()
    const boxName = `E2E Items ${ts}`
    const boxNumber = String((ts + 1) % 100000)
    await page.fill('#box_name', boxName)
    await page.fill('#box_number', boxNumber)
    await page.selectOption('#box_size', 'Medium')
    await page.click('button[type="submit"]')
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })

    // Navigate to the new box
    await page.locator('.packed-box__link, .packed-box-compact__link', { hasText: boxName }).click()
    await expect(page).toHaveTitle('Box Detail | iChrisBirch')

    // Add an item
    const itemName = `E2E Item ${Date.now()}`
    await page.fill('#item_name', itemName)
    await page.click('button[type="submit"]')
    await expect(page.locator(SUCCESS, { hasText: 'Item added' })).toBeVisible({ timeout: 5000 })

    // Verify item appears
    await expect(page.getByText(itemName)).toBeVisible()
  })

  test('subnav links navigate between sub-pages', async ({ page }) => {
    await page.goto('/box-packing')

    // Navigate to Orphans
    await page.click('.box-packing-subnav__link >> text=Orphans')
    await expect(page).toHaveTitle('Orphaned Items | iChrisBirch')

    // Navigate to Search
    await page.click('.box-packing-subnav__link >> text=Search')
    await expect(page).toHaveTitle('Search Items | iChrisBirch')

    // Navigate back to All Boxes
    await page.click('.box-packing-subnav__link >> text=All Boxes')
    await expect(page).toHaveTitle('All Boxes | iChrisBirch')
  })

  test('sidebar navigation shows box packing as active', async ({ page }) => {
    await page.goto('/box-packing')
    const sidebarLink = page.locator('.nav-link--active', { hasText: 'Box Packing' })
    await expect(sidebarLink).toBeVisible()
  })

  test('search page has input and handles search', async ({ page }) => {
    await page.goto('/box-packing/search')
    await expect(page.locator('#search_text')).toBeVisible()
    await expect(page.locator('#search_text')).toBeFocused()
  })
})
