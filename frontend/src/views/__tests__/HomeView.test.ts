import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import HomeView from '../HomeView.vue'
import type { User } from '@/api/client'

const testUser: User = {
  id: 1,
  alternative_id: 100,
  name: 'Chris Birch',
  email: 'admin@icb.com',
  is_admin: true,
  created_on: '2024-01-01T00:00:00Z',
  last_login: '2026-03-29T12:00:00Z',
  preferences: { theme_color: 'blue', font_family: 'Inter', dark_mode: true, notifications: true, dashboard_layout: [] },
}

const nonAdminUser: User = {
  ...testUser,
  id: 2,
  is_admin: false,
}

function createWrapper(authState: Record<string, unknown> = {}) {
  return mount(HomeView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            auth: {
              user: null,
              ...authState,
            },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
    },
  })
}

describe('HomeView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders heading and tagline', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('Chris Birch')
    expect(wrapper.text()).toContain('Data Engineer')
    expect(wrapper.text()).toContain('Nothing Is Truly Gone')
    expect(wrapper.text()).toContain('git log --all --full-history')
  })

  it('renders project links for non-admin users', () => {
    const wrapper = createWrapper({ user: nonAdminUser })
    const labels = wrapper.findAll('.home-link-label').map((el) => el.text())
    expect(labels).toEqual(['Code', 'Chat', 'API', 'Docs'])
  })

  it('renders project and service links for admin users', () => {
    const wrapper = createWrapper({ user: testUser })
    const labels = wrapper.findAll('.home-link-label').map((el) => el.text())
    expect(labels).toContain('Code')
    expect(labels).toContain('Monitor')
    expect(labels).toContain('Files')
    expect(labels).toContain('Learning')
    expect(labels.length).toBe(11)
  })

  it('all links open in new tabs', () => {
    const wrapper = createWrapper({ user: testUser })
    const links = wrapper.findAll('.home-links a')
    for (const link of links) {
      expect(link.attributes('target')).toBe('_blank')
    }
  })

  it('renders 4 project links when no user loaded', () => {
    const wrapper = createWrapper()
    const labels = wrapper.findAll('.home-link-label').map((el) => el.text())
    expect(labels).toEqual(['Code', 'Chat', 'API', 'Docs'])
  })
})
