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

const testApiKeys = [
  {
    id: 1,
    name: 'MCP Key',
    key_prefix: 'icb_abcd',
    created_at: '2026-01-15T00:00:00Z',
    last_used_at: null,
    revoked_at: null,
  },
  {
    id: 2,
    name: 'Old Key',
    key_prefix: 'icb_efgh',
    created_at: '2025-06-01T00:00:00Z',
    last_used_at: '2025-12-01T00:00:00Z',
    revoked_at: '2026-01-01T00:00:00Z',
  },
]

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
    expect(store.apiKeys).toEqual([])
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
    expect(store.apiKeys).toEqual([])
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

  // --- fetchApiKeys ---

  it('fetches API keys successfully', async () => {
    mockApi.get.mockResolvedValueOnce({ data: testApiKeys })
    const store = useAuthStore()
    await store.fetchApiKeys()
    expect(mockApi.get).toHaveBeenCalledWith('/api-keys/')
    expect(store.apiKeys).toEqual(testApiKeys)
    expect(store.error).toBeNull()
  })

  it('handles fetchApiKeys failure', async () => {
    const apiError = new ApiError({ message: 'Server Error', detail: 'Database error', status: 500 })
    mockApi.get.mockRejectedValueOnce(apiError)
    const store = useAuthStore()
    await expect(store.fetchApiKeys()).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.apiKeys).toEqual([])
  })

  // --- createApiKey ---

  it('creates API key and adds to list', async () => {
    const createdKey = { ...testApiKeys[0], key: 'icb_abcdefgh1234567890' }
    mockApi.post.mockResolvedValueOnce({ data: createdKey })
    const store = useAuthStore()
    const result = await store.createApiKey('MCP Key')
    expect(mockApi.post).toHaveBeenCalledWith('/api-keys/', { name: 'MCP Key' })
    expect(result.key).toBe('icb_abcdefgh1234567890')
    expect(store.apiKeys).toHaveLength(1)
    // Local list should not contain the full key
    expect(store.apiKeys[0]).not.toHaveProperty('key')
    expect(store.error).toBeNull()
  })

  it('handles createApiKey failure', async () => {
    const apiError = new ApiError({ message: 'Bad Request', detail: 'Name required', status: 400 })
    mockApi.post.mockRejectedValueOnce(apiError)
    const store = useAuthStore()
    await expect(store.createApiKey('')).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.apiKeys).toEqual([])
  })

  // --- revokeApiKey ---

  it('revokes API key and updates local state', async () => {
    mockApi.delete.mockResolvedValueOnce({})
    const store = useAuthStore()
    store.apiKeys = [...testApiKeys]
    await store.revokeApiKey(1)
    expect(mockApi.delete).toHaveBeenCalledWith('/api-keys/1/')
    expect(store.apiKeys[0].revoked_at).not.toBeNull()
    expect(store.error).toBeNull()
  })

  it('handles revokeApiKey failure', async () => {
    const apiError = new ApiError({ message: 'Not Found', detail: 'Key not found', status: 404 })
    mockApi.delete.mockRejectedValueOnce(apiError)
    const store = useAuthStore()
    store.apiKeys = [...testApiKeys]
    await expect(store.revokeApiKey(999)).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
  })

  // --- resetTaskPriorities ---

  it('resets task priorities successfully', async () => {
    mockApi.post.mockResolvedValueOnce({ data: { message: 'Reset priorities for 5 tasks' } })
    const store = useAuthStore()
    const result = await store.resetTaskPriorities()
    expect(mockApi.post).toHaveBeenCalledWith('/tasks/reset-priorities/')
    expect(result.message).toBe('Reset priorities for 5 tasks')
    expect(store.error).toBeNull()
  })

  it('handles resetTaskPriorities failure', async () => {
    const apiError = new ApiError({ message: 'Server Error', detail: 'Database error', status: 500 })
    mockApi.post.mockRejectedValueOnce(apiError)
    const store = useAuthStore()
    await expect(store.resetTaskPriorities()).rejects.toThrow(ApiError)
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
