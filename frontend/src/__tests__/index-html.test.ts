import { describe, expect, it } from 'vitest'
import html from '../../index.html?raw'

const head = new DOMParser().parseFromString(html, 'text/html').head

describe('index.html', () => {
  // A manifest link is fetched without cookies unless it asks for them, and in
  // production every path sits behind the login, so Chrome would install a bookmark.
  it('sends the session cookie when Chrome fetches the manifest to install the app', () => {
    const manifest = head.querySelector('link[rel="manifest"]')
    expect(manifest?.getAttribute('crossorigin')).toBe('use-credentials')
  })
})
