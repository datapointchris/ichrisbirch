import { test, expect } from '@playwright/test'

const SUCCESS = '.flash-messages__message--success'
const ERROR = '.flash-messages__message--error'

// Smoke tests only — interaction-heavy tests (tab switching, completed toggle,
// scheduler settings form, modal fields) are covered by component integration
// tests in src/views/__tests__/AutoFunView.test.ts

test.describe('AutoFun Page', () => {
  test('API calls succeed through Traefik routing (CORS check)', async ({ page }) => {
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/autofun')
    await expect(page.getByTestId('autofun-tab-list')).toBeVisible({ timeout: 10000 })
    await expect(page.locator(ERROR)).not.toBeVisible()
    expect(apiErrors).toEqual([])
  })

  test('loads the page with correct title and tab navigation', async ({ page }) => {
    await page.goto('/autofun')
    await expect(page).toHaveTitle('AutoFun | iChrisBirch')
    await expect(page.getByTestId('autofun-tab-list')).toBeVisible()
    await expect(page.getByTestId('autofun-tab-scheduler')).toBeVisible()
  })

  test('sidebar navigation to autofun works', async ({ page }) => {
    await page.goto('/autofun')
    await expect(page).toHaveTitle('AutoFun | iChrisBirch')
    const sidebarLink = page.locator('.nav-link--active', { hasText: 'AutoFun' })
    await expect(sidebarLink).toBeVisible()
  })

  test('adds and deletes a fun activity', async ({ page }) => {
    await page.goto('/autofun')
    await expect(page.getByTestId('autofun-tab-list')).toBeVisible({ timeout: 10000 })

    const name = `E2E AutoFun ${Date.now()}`
    await page.getByTestId('autofun-add-button').click()
    await expect(page.getByTestId('add-edit-modal')).toBeVisible({ timeout: 5000 })
    await page.getByTestId('autofun-name-input').fill(name)
    await page.getByTestId('autofun-submit-button').click()
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })

    const item = page.getByTestId('autofun-item').filter({ hasText: name })
    await expect(item).toBeVisible()

    await item.getByTestId('autofun-delete-button').click()
    await expect(page.locator(SUCCESS).first()).toBeVisible({ timeout: 5000 })
    await expect(item).not.toBeVisible()
  })
})
