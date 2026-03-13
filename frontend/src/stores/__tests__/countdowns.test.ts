import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useCountdownsStore } from '../countdowns'
import { ApiError } from '@/api/errors'

// Mock the API client — all store tests go through this mock
vi.mock('@/api/client', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

// Import the mocked api so we can set return values per test
import { api } from '@/api/client'
const mockApi = vi.mocked(api)

// Reusable test data matching the Countdown interface
const testCountdowns = [
  { id: 1, name: 'Birthday', due_date: '2026-12-25', notes: 'Party planning' },
  { id: 2, name: 'Deadline', due_date: '2026-06-15' },
  { id: 3, name: 'Trip', due_date: '2026-09-01', notes: 'Pack bags' },
]

describe('useCountdownsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  // --- Initial state ---

  it('initializes with empty state', () => {
    const store = useCountdownsStore()
    expect(store.countdowns).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  // --- fetchAll ---

  it('fetches countdowns from API and sets state', async () => {
    mockApi.get.mockResolvedValue({ data: testCountdowns })
    const store = useCountdownsStore()

    await store.fetchAll()

    expect(mockApi.get).toHaveBeenCalledWith('/countdowns/')
    expect(store.countdowns).toEqual(testCountdowns)
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
    const store = useCountdownsStore()

    const fetchPromise = store.fetchAll()
    expect(store.loading).toBe(true)

    resolvePromise({ data: [] })
    await fetchPromise
    expect(store.loading).toBe(false)
  })

  it('sets error state on fetch failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Internal Server Error', status: 500 })
    mockApi.get.mockRejectedValue(apiError)
    const store = useCountdownsStore()

    await expect(store.fetchAll()).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.error!.status).toBe(500)
    expect(store.loading).toBe(false)
  })

  it('clears previous error on successful fetch', async () => {
    const store = useCountdownsStore()
    store.error = new ApiError({ message: 'old error', detail: 'old' }) as typeof store.error

    mockApi.get.mockResolvedValue({ data: [] })
    await store.fetchAll()
    expect(store.error).toBeNull()
  })

  // --- create ---

  it('creates a countdown and adds it to the list', async () => {
    const newCountdown = { id: 4, name: 'New Year', due_date: '2027-01-01', notes: null }
    mockApi.post.mockResolvedValue({ data: newCountdown })
    const store = useCountdownsStore()

    const result = await store.create({ name: 'New Year', due_date: '2027-01-01' })

    expect(mockApi.post).toHaveBeenCalledWith('/countdowns/', { name: 'New Year', due_date: '2027-01-01' })
    expect(result).toEqual(newCountdown)
    expect(store.countdowns).toContainEqual(newCountdown)
  })

  it('sets error state on create failure', async () => {
    const apiError = new ApiError({
      message: 'API 422',
      detail: 'Validation error',
      status: 422,
      validationErrors: [{ field: 'due_date', message: 'Must be in the future' }],
    })
    mockApi.post.mockRejectedValue(apiError)
    const store = useCountdownsStore()

    await expect(store.create({ name: 'Bad', due_date: '2020-01-01' })).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.error!.validationErrors).toHaveLength(1)
    expect(store.countdowns).toEqual([]) // not added on failure
  })

  // --- update ---

  it('updates a countdown in place', async () => {
    const updated = { id: 1, name: 'Updated Birthday', due_date: '2026-12-25', notes: 'New notes' }
    mockApi.patch.mockResolvedValue({ data: updated })
    const store = useCountdownsStore()
    store.countdowns = [...testCountdowns]

    const result = await store.update(1, { name: 'Updated Birthday', notes: 'New notes' })

    expect(mockApi.patch).toHaveBeenCalledWith('/countdowns/1/', { name: 'Updated Birthday', notes: 'New notes' })
    expect(result).toEqual(updated)
    expect(store.countdowns.find((c) => c.id === 1)!.name).toBe('Updated Birthday')
  })

  it('sets error state on update failure', async () => {
    const apiError = new ApiError({ message: 'API 404', detail: 'Countdown not found', status: 404 })
    mockApi.patch.mockRejectedValue(apiError)
    const store = useCountdownsStore()

    await expect(store.update(999, { name: 'Ghost' })).rejects.toThrow(ApiError)
    expect(store.error!.status).toBe(404)
  })

  // --- remove ---

  it('removes a countdown from the list', async () => {
    mockApi.delete.mockResolvedValue({})
    const store = useCountdownsStore()
    store.countdowns = [...testCountdowns]

    await store.remove(2)

    expect(mockApi.delete).toHaveBeenCalledWith('/countdowns/2/')
    expect(store.countdowns).toHaveLength(2)
    expect(store.countdowns.find((c) => c.id === 2)).toBeUndefined()
  })

  it('does not remove on delete failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Database error', status: 500 })
    mockApi.delete.mockRejectedValue(apiError)
    const store = useCountdownsStore()
    store.countdowns = [...testCountdowns]

    await expect(store.remove(1)).rejects.toThrow(ApiError)
    expect(store.countdowns).toHaveLength(3) // unchanged
    expect(store.error!.status).toBe(500)
  })

  // --- sortedCountdowns ---

  it('sorts countdowns by due_date ascending', () => {
    const store = useCountdownsStore()
    store.countdowns = [...testCountdowns]
    const sorted = store.sortedCountdowns
    expect(sorted[0]!.name).toBe('Deadline') // June
    expect(sorted[1]!.name).toBe('Trip') // September
    expect(sorted[2]!.name).toBe('Birthday') // December
  })

  // --- clearError ---

  it('clears error state', () => {
    const store = useCountdownsStore()
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
    const store = useCountdownsStore()

    await expect(store.fetchAll()).rejects.toThrow(ApiError)
    expect(store.error!.isNetworkError).toBe(true)
    expect(store.error!.userMessage).toBe('Unable to reach the server. Check your connection.')
  })
})
