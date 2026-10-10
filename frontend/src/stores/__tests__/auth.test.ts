import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../auth'
import { ApiError } from '@/api/errors'

vi.mock('@/api/client', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

import { api } from '@/api/client'
const mockApi = vi.mocked(api)

const testPreferences = {
  theme_color: 'turquoise',
  font_family: 'ubuntu-mono',
  dark_mode: true,
  notifications: false,
  dashboard_layout: [['tasks_priority', 'countdowns', 'events']],
}

const testUser = {
  id: 1,
  alternative_id: 100,
  name: 'Test User',
  email: 'test@example.com',
  is_admin: false,
  created_on: '2026-01-01T00:00:00Z',
  last_login: '2026-03-01T00:00:00Z',
  preferences: testPreferences,
}

const testAdminUser = {
  ...testUser,
  id: 2,
  name: 'Admin User',
  email: 'admin@example.com',
  is_admin: true,
}

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  // --- Initial state ---

  it('starts unauthenticated', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
    expect(store.isAdmin).toBe(false)
    expect(store.user).toBeNull()
    expect(store.preferences).toBeNull()
    expect(store.error).toBeNull()
  })

  // --- setUser / clear ---

  it('sets user and updates computed properties', () => {
    const store = useAuthStore()
    store.setUser(testUser)
    expect(store.isAuthenticated).toBe(true)
    expect(store.isAdmin).toBe(false)
    expect(store.user?.name).toBe('Test User')
    expect(store.preferences).toEqual(testPreferences)
  })

  it('sets admin user correctly', () => {
    const store = useAuthStore()
    store.setUser(testAdminUser)
    expect(store.isAdmin).toBe(true)
  })

  it('clears user state', () => {
    const store = useAuthStore()
    store.setUser(testUser)
    store.clear()
    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
    expect(store.error).toBeNull()
  })

  // --- fetchCurrentUser ---

  it('fetches current user successfully', async () => {
    mockApi.get.mockResolvedValueOnce({ data: testUser })
    const store = useAuthStore()
    await store.fetchCurrentUser()
    expect(mockApi.get).toHaveBeenCalledWith('/users/me/')
    expect(store.user).toEqual(testUser)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('sets loading state during fetchCurrentUser', async () => {
    let resolvePromise: (value: unknown) => void
    const promise = new Promise((resolve) => {
      resolvePromise = resolve
    })
    mockApi.get.mockReturnValueOnce(promise as never)
    const store = useAuthStore()
    const fetchPromise = store.fetchCurrentUser()
    expect(store.loading).toBe(true)
    resolvePromise!({ data: testUser })
    await fetchPromise
    expect(store.loading).toBe(false)
  })

  it('handles fetchCurrentUser failure', async () => {
    const apiError = new ApiError({ message: 'Unauthorized', detail: 'Not authenticated', status: 401 })
    mockApi.get.mockRejectedValueOnce(apiError)
    const store = useAuthStore()
    await expect(store.fetchCurrentUser()).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.user).toBeNull()
    expect(store.loading).toBe(false)
  })

  // --- updatePreferences ---

  it('updates preferences successfully', async () => {
    const updatedUser = { ...testUser, preferences: { ...testPreferences, theme_color: 'blue' } }
    mockApi.patch.mockResolvedValueOnce({ data: updatedUser })
    const store = useAuthStore()
    store.setUser(testUser)
    await store.updatePreferences({ theme_color: 'blue' })
    expect(mockApi.patch).toHaveBeenCalledWith('/users/me/preferences/', { theme_color: 'blue' })
    expect(store.user?.preferences.theme_color).toBe('blue')
    expect(store.error).toBeNull()
  })

  it('handles updatePreferences failure', async () => {
    const apiError = new ApiError({ message: 'Bad Request', detail: 'Invalid preference', status: 400 })
    mockApi.patch.mockRejectedValueOnce(apiError)
    const store = useAuthStore()
    store.setUser(testUser)
    await expect(store.updatePreferences({ theme_color: 'invalid' })).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
  })

  // --- reorderTasks ---

  it('reorders tasks successfully', async () => {
    mockApi.post.mockResolvedValueOnce({ data: { message: 'Reordered 5 tasks' } })
    const store = useAuthStore()
    const result = await store.reorderTasks()
    expect(mockApi.post).toHaveBeenCalledWith('/tasks/reorder/')
    expect(result.message).toBe('Reordered 5 tasks')
    expect(store.error).toBeNull()
  })

  it('handles reorderTasks failure', async () => {
    const apiError = new ApiError({ message: 'Server Error', detail: 'Database error', status: 500 })
    mockApi.post.mockRejectedValueOnce(apiError)
    const store = useAuthStore()
    await expect(store.reorderTasks()).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
  })

  // --- clearError ---

  it('clears error state', async () => {
    const apiError = new ApiError({ message: 'Error', detail: 'Something failed', status: 500 })
    mockApi.get.mockRejectedValueOnce(apiError)
    const store = useAuthStore()
    await expect(store.fetchCurrentUser()).rejects.toThrow()
    expect(store.error).not.toBeNull()
    store.clearError()
    expect(store.error).toBeNull()
  })
})
