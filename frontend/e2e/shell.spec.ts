import { test, expect } from '@playwright/test'

// The app shell: the sidebar on both screens, and where a phone opens. The
// `phone` project in playwright.config.ts runs this file at phone size.
// home.spec.ts pins a desktop visit to `/` staying on Home.

test.describe('Sidebar', () => {
  test('every link in the sidebar can be scrolled into view', async ({ page, isMobile }) => {
    await page.goto('/today')
    if (isMobile) await page.getByTestId('sidebar-open-button').click()
    const links = page.getByRole('complementary').getByRole('link')
    const count = await links.count()
    expect(count).toBeGreaterThan(0)
    for (let i = 0; i < count; i++) {
      await links.nth(i).scrollIntoViewIfNeeded()
      await expect(links.nth(i), `link ${i + 1} of ${count}`).toBeInViewport({ ratio: 0.9 })
    }
  })

  test('a hovered link pops past the sidebar edge whole, and the page beside it still takes clicks', async ({ page, isMobile }) => {
    test.skip(isMobile, 'a phone has no hover')
    await page.goto('/today')
    const sidebarEdge = await page.getByRole('complementary').evaluate((el) => el.getBoundingClientRect().right)
    const home = page.getByTestId('sidebar-/')

    const resting = await home.boundingBox()
    const besideLink = await page.evaluate(({ x, y }) => !document.elementFromPoint(x, y)?.closest('.sidebar__nav'), {
      x: sidebarEdge + 20,
      y: resting!.y + resting!.height / 2,
    })
    expect(besideLink, 'the page beside a resting link takes the click').toBe(true)

    await home.hover()
    await expect.poll(async () => (await home.boundingBox())!.width).toBeGreaterThan(resting!.width * 1.15)
    const popped = (await home.boundingBox())!
    expect(popped.x + popped.width).toBeGreaterThan(sidebarEdge)
    const tipShows = await page.evaluate(({ x, y }) => document.elementFromPoint(x, y)?.closest('[data-testid="sidebar-/"]') !== null, {
      x: popped.x + popped.width - 4,
      y: popped.y + popped.height / 2,
    })
    expect(tipShows, 'the tip of the hovered link is drawn, not clipped').toBe(true)
  })
})

test.describe('Phone', () => {
  test('a phone that opens the site on / lands on Today, and the menu still reaches Home', async ({ page, isMobile }) => {
    test.skip(!isMobile, 'a desktop visit stays on Home')
    await page.goto('/')
    await expect(page).toHaveURL(/\/today$/)

    await page.getByTestId('sidebar-open-button').click()
    await page.getByTestId('sidebar-/').click()
    await expect(page).toHaveURL(/\/$/)
  })
})
