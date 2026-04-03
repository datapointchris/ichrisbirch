import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAutoFunStore } from '../autofun'
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

const testItems = [
  {
    id: 1,
    name: 'Go to the Japanese Tea Garden',
    notes: 'Free on weekday mornings',
    is_completed: false,
    added_date: '2026-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: 'Hike the Dipsea Trail',
    is_completed: false,
    added_date: '2026-01-05T00:00:00Z',
  },
  {
    id: 3,
    name: 'Watch a film at the Castro',
    is_completed: true,
    completed_date: '2026-02-14T00:00:00Z',
    added_date: '2026-01-10T00:00:00Z',
  },
]

describe('useAutoFunStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  // --- Initial state ---

  it('initializes with empty state', () => {
    const store = useAutoFunStore()
    expect(store.items).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  // --- fetchAll ---

  it('fetches items from API and sets state', async () => {
    mockApi.get.mockResolvedValue({ data: testItems })
    const store = useAutoFunStore()

    await store.fetchAll()

    expect(mockApi.get).toHaveBeenCalledWith('/autofun/')
    expect(store.items).toEqual(testItems)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('sets loading state during fetch', async () => {
    let resolvePromise!: (value: unknown) => void
    mockApi.get.mockReturnValue(
      new Promise((resolve) => {
        resolvePromise = resolve
      })
    )
    const store = useAutoFunStore()

    const fetchPromise = store.fetchAll()
    expect(store.loading).toBe(true)

    resolvePromise({ data: [] })
    await fetchPromise
    expect(store.loading).toBe(false)
  })

  it('sets error state on fetch failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Internal Server Error', status: 500 })
    mockApi.get.mockRejectedValue(apiError)
    const store = useAutoFunStore()

    await expect(store.fetchAll()).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.loading).toBe(false)
  })

  it('clears previous error on successful fetch', async () => {
    const store = useAutoFunStore()
    store.error = new ApiError({ message: 'old', detail: 'old' }) as typeof store.error

    mockApi.get.mockResolvedValue({ data: [] })
    await store.fetchAll()
    expect(store.error).toBeNull()
  })

  // --- create ---

  it('creates an item and prepends it to the list', async () => {
    const created = { id: 4, name: 'New activity', is_completed: false, added_date: '2026-04-01T00:00:00Z' }
    mockApi.post.mockResolvedValue({ data: created })
    const store = useAutoFunStore()
    store.items = [...testItems]

    await store.create({ name: 'New activity' })

    expect(mockApi.post).toHaveBeenCalledWith('/autofun/', { name: 'New activity' })
    expect(store.items[0]).toEqual(created)
    expect(store.items).toHaveLength(4)
  })

  it('sets error on create failure', async () => {
    const apiError = new ApiError({ message: 'API 422', detail: 'Validation error', status: 422 })
    mockApi.post.mockRejectedValue(apiError)
    const store = useAutoFunStore()

    await expect(store.create({ name: '' })).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.items).toHaveLength(0)
  })

  // --- update ---

  it('updates an item in place', async () => {
    const updated = { ...testItems[0], name: 'Updated name' }
    mockApi.patch.mockResolvedValue({ data: updated })
    const store = useAutoFunStore()
    store.items = [...testItems]

    await store.update(1, { name: 'Updated name' })

    expect(mockApi.patch).toHaveBeenCalledWith('/autofun/1/', { name: 'Updated name' })
    expect(store.items.find((i) => i.id === 1)!.name).toBe('Updated name')
  })

  // --- remove ---

  it('removes an item from the list', async () => {
    mockApi.delete.mockResolvedValue({})
    const store = useAutoFunStore()
    store.items = [...testItems]

    await store.remove(2)

    expect(mockApi.delete).toHaveBeenCalledWith('/autofun/2/')
    expect(store.items).toHaveLength(2)
    expect(store.items.find((i) => i.id === 2)).toBeUndefined()
  })

  it('does not remove on delete failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Error', status: 500 })
    mockApi.delete.mockRejectedValue(apiError)
    const store = useAutoFunStore()
    store.items = [...testItems]

    await expect(store.remove(1)).rejects.toThrow(ApiError)
    expect(store.items).toHaveLength(3)
  })

  // --- computed: activeItems / completedItems ---

  it('activeItems returns only non-completed items', () => {
    const store = useAutoFunStore()
    store.items = [...testItems]
    expect(store.activeItems).toHaveLength(2)
    expect(store.activeItems.every((i) => !i.is_completed)).toBe(true)
  })

  it('completedItems returns only completed items', () => {
    const store = useAutoFunStore()
    store.items = [...testItems]
    expect(store.completedItems).toHaveLength(1)
    expect(store.completedItems[0]!.name).toBe('Watch a film at the Castro')
  })

  // --- clearError ---

  it('clears error state', () => {
    const store = useAutoFunStore()
    store.error = new ApiError({ message: 'err', detail: 'err' }) as typeof store.error
    store.clearError()
    expect(store.error).toBeNull()
  })

  // --- network error ---

  it('handles network errors with structured ApiError', async () => {
    const networkError = new ApiError({
      message: 'Network error',
      detail: 'Unable to reach the server. Check your connection.',
      isNetworkError: true,
    })
    mockApi.get.mockRejectedValue(networkError)
    const store = useAutoFunStore()

    await expect(store.fetchAll()).rejects.toThrow(ApiError)
    expect(store.error!.isNetworkError).toBe(true)
  })
})
