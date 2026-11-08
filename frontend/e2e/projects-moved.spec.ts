import { test, expect } from '@playwright/test'
import { PROJECTS_APP_URL } from '../src/components/sidebarLinks'

// Projects live in the projects app at its own host. No component test covers
// this: the redirect is Traefik's, and the link is one attribute.

test.describe('Projects', () => {
  test('the sidebar link leaves for the projects app', async ({ page }) => {
    await page.goto('/tasks')
    await expect(page.getByTestId('sidebar-/projects')).toHaveAttribute('href', PROJECTS_APP_URL)
  })

  test('the old address forwards to the projects app', async ({ request }) => {
    const response = await request.get('/projects', { maxRedirects: 0 })
    expect(response.status()).toBe(301)
    expect(response.headers()['location']).toBe(PROJECTS_APP_URL)
  })
})
