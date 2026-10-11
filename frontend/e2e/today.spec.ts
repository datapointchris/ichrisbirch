import { test, expect } from '@playwright/test'

const ERROR = '.flash-messages__message--error'

// Smoke tests only — check-off timing, undo, the category prompt and the day
// rollover are covered by component integration tests in
// src/views/__tests__/TodayView.test.ts. The `phone` project in
// playwright.config.ts runs this file at phone size too.

test.describe('Today Page', () => {
  test('API calls succeed through Traefik routing (CORS check)', async ({ page }) => {
    const apiErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error' && msg.text().includes('request_')) {
        apiErrors.push(msg.text())
      }
    })

    await page.goto('/today')
    await expect(page.getByTestId('today-add-input')).toBeVisible({ timeout: 10000 })
    await expect(page.getByTestId('today-tasks')).toBeVisible()
    await expect(page.locator(ERROR)).not.toBeVisible()
    expect(apiErrors).toEqual([])
  })

  test('loads the page', async ({ page }) => {
    await page.goto('/today')
    await expect(page).toHaveTitle('Today | iChrisBirch')
  })

  test('adds a task, then completing the first task moves it to done today and tapping it reopens it', async ({ page }) => {
    await page.goto('/today')
    await page.getByTestId('today-mode-task').click()
    await page.getByTestId('today-category').filter({ hasText: 'Chore' }).click()

    const name = `e2e today task ${Date.now()}`
    await page.getByTestId('today-add-input').fill(name)
    await page.getByTestId('today-add-input').press('Enter')
    await expect(page.getByTestId('today-add-note')).toContainText(name)

    const first = page.getByTestId('today-task').first()
    const firstName = (await first.locator('.today-row__name').textContent())!.trim()
    await first.getByTestId('today-task-complete').click()

    const done = page.getByTestId('today-task-done').filter({ hasText: firstName })
    await expect(done).toBeVisible({ timeout: 5000 })
    await done.click()
    await expect(done).not.toBeVisible({ timeout: 5000 })
    await expect(page.getByTestId('today-task').filter({ hasText: firstName })).toBeVisible()
  })

  test('adds to the shopping list from the shopping mode', async ({ page }) => {
    await page.goto('/today')
    await page.getByTestId('today-mode-shopping').click()

    const name = `e2e today item ${Date.now()}`
    await page.getByTestId('today-add-input').fill(name)
    await page.getByTestId('today-add-input').press('Enter')
    await expect(page.getByTestId('today-add-note')).toContainText(name)
  })

  test('on a phone, the page fits the screen and every control is big enough for a finger', async ({ page, isMobile }) => {
    test.skip(!isMobile, 'the measurement is of the phone layout')
    await page.goto('/today')
    await expect(page.getByTestId('today-tasks')).toBeVisible({ timeout: 10000 })
    await expect(page.locator('.today-block__empty, [data-testid="today-task"]').first()).toBeVisible()

    const fit = await page.evaluate(() => {
      const root = document.documentElement
      // A tap on a control lands on its box, so a box under 44px either way is missed.
      const small = [...document.querySelectorAll<HTMLElement>('[data-testid="today-page"] :is(button, a, input)')]
        .filter((el) => el.offsetParent !== null)
        .filter((el) => {
          const box = el.getBoundingClientRect()
          return box.width < 43.5 || box.height < 43.5
        })
        .map((el) => el.dataset.testid ?? el.textContent?.trim() ?? el.tagName)
      return { overflow: root.scrollWidth - root.clientWidth, small }
    })
    expect(fit.overflow).toBe(0)
    expect(fit.small).toEqual([])
  })

  test('sidebar navigation to today works', async ({ page, isMobile }) => {
    await page.goto('/today')
    if (isMobile) await page.getByTestId('sidebar-open-button').click()

    await expect(page.locator('.nav-link--active', { hasText: 'Today' })).toBeVisible()
  })
})
