import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/api/client', () => ({
  api: { get: vi.fn(), patch: vi.fn() },
}))

import { api } from '@/api/client'
import type { User, UserPreferences } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { displayZone, useDisplayZone } from '../displayZone'
import { browserTimezone } from '../useWallClock'

const mockApi = vi.mocked(api)

function userIn(timezone: string | null): User {
  const preferences = {
    theme_color: 'blue',
    font_family: 'ubuntu-mono',
    dark_mode: true,
    notifications: false,
    dashboard_layout: [],
    timezone,
  }
  return {
    id: 1,
    alternative_id: 1,
    name: 'Zone',
    email: 'zone@example.com',
    is_admin: false,
    created_on: '2026-01-01T00:00:00Z',
    preferences: preferences as UserPreferences,
  }
}

describe('useDisplayZone', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('shows dates in the zone the user chose', () => {
    const auth = useAuthStore()
    auth.setUser(userIn('Asia/Tokyo'))

    useDisplayZone()

    expect(displayZone()).toBe('Asia/Tokyo')
    expect(mockApi.patch).not.toHaveBeenCalled()
  })

  it('records the browser zone for a user who has never chosen one', () => {
    mockApi.patch.mockResolvedValue({ data: userIn(browserTimezone()) })
    const auth = useAuthStore()
    auth.setUser(userIn(null))

    useDisplayZone()

    expect(displayZone()).toBe(browserTimezone())
    expect(mockApi.patch).toHaveBeenCalledWith('/users/me/preferences/', { timezone: browserTimezone() })
  })
})
