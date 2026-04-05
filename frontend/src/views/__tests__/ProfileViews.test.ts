import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import ProfileView from '../ProfileView.vue'
import { useAuthStore } from '@/stores/auth'
import type { User } from '@/api/client'

vi.mock('@/composables/useNotifications', () => ({
  useNotifications: () => ({
    show: vi.fn(),
    close: vi.fn(),
    closeAll: vi.fn(),
    notifications: { value: [] },
  }),
}))

vi.mock('@/composables/formatDate', () => ({
  formatDate: (date: string) => `formatted:${date}`,
}))

vi.mock('@/composables/useTheme', () => ({
  applyTheme: vi.fn(),
  applyFont: vi.fn(),
  applyAccentHue: vi.fn(),
  themes: [
    { id: 'red', name: 'Red', type: 'color', swatch: '#f00' },
    { id: 'blue', name: 'Blue', type: 'color', swatch: '#00f' },
    { id: 'dracula', name: 'Dracula', type: 'named', swatch: '#282a36' },
  ],
  fonts: [
    { id: 'inter', name: 'Inter' },
    { id: 'ubuntu-mono', name: 'Ubuntu Mono' },
  ],
}))

const testUser: User = {
  id: 1,
  alternative_id: 100,
  name: 'Chris Birch',
  email: 'chris@example.com',
  is_admin: true,
  created_on: '2024-01-01T00:00:00Z',
  last_login: '2026-03-29T12:00:00Z',
  preferences: {
    theme_color: 'blue',
    font_family: 'Inter',
    dark_mode: true,
    notifications: true,
    dashboard_layout: [],
  },
}

function createWrapper(storeState: Record<string, unknown> = {}) {
  return mount(ProfileView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            auth: {
              user: null,
              preferences: null,
              apiKeys: [],
              loading: false,
              error: null,
              ...storeState,
            },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
    },
  })
}

describe('ProfileView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls fetchCurrentUser on mount when no user loaded', () => {
    createWrapper()
    const store = useAuthStore()
    expect(store.fetchCurrentUser).toHaveBeenCalledOnce()
  })

  it('does not fetch when user is already loaded', () => {
    createWrapper({ user: testUser })
    const store = useAuthStore()
    expect(store.fetchCurrentUser).not.toHaveBeenCalled()
  })

  it('renders loading state', () => {
    const wrapper = createWrapper({ loading: true })
    expect(wrapper.text()).toContain('Loading...')
  })

  it('renders error when no user', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('Unable to load profile')
  })

  it('renders user info when loaded', () => {
    const wrapper = createWrapper({ user: testUser, preferences: testUser.preferences })
    expect(wrapper.text()).toContain('Chris Birch')
    expect(wrapper.text()).toContain('chris@example.com')
    expect(wrapper.text()).toContain('Admin')
  })

  it('renders appearance settings', () => {
    const wrapper = createWrapper({ user: testUser, preferences: testUser.preferences })
    expect(wrapper.text()).toContain('Appearance')
    const swatches = wrapper.findAll('.theme-colors__swatch')
    expect(swatches.length).toBeGreaterThan(0)
  })

  it('renders font selector', () => {
    const wrapper = createWrapper({ user: testUser, preferences: testUser.preferences })
    expect(wrapper.text()).toContain('Font')
  })

  it('renders API keys section', () => {
    const wrapper = createWrapper({ user: testUser, preferences: testUser.preferences })
    expect(wrapper.text()).toContain('Personal API Keys')
  })
})
