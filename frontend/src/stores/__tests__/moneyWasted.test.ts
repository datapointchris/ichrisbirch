import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useMoneyWastedStore } from '../moneyWasted'
import { ApiError } from '@/api/errors'

vi.mock('@/api/client', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}))

import { api } from '@/api/client'
const mockApi = vi.mocked(api)

const testItems = [
  {
    id: 1,
    item: 'Expensive Blender',
    amount: 149.99,
    date_purchased: '2025-06-15',
    date_wasted: '2026-01-10',
    notes: 'Never used it',
  },
  {
    id: 2,
    item: 'Gym Membership',
    amount: 480.0,
    date_wasted: '2026-02-01',
  },
  {
    id: 3,
    item: 'Online Course',
    amount: 29.99,
    date_purchased: '2025-12-01',
    date_wasted: '2026-03-05',
    notes: 'Only watched intro',
  },
]

describe('useMoneyWastedStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  // --- Initial state ---

  it('initializes with empty state', () => {
    const store = useMoneyWastedStore()
    expect(store.items).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  // --- fetchAll ---

  it('fetches items from API and sets state', async () => {
    mockApi.get.mockResolvedValue({ data: testItems })
    const store = useMoneyWastedStore()

    await store.fetchAll()

    expect(mockApi.get).toHaveBeenCalledWith('/money-wasted/')
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
    const store = useMoneyWastedStore()

    const fetchPromise = store.fetchAll()
    expect(store.loading).toBe(true)

    resolvePromise({ data: [] })
    await fetchPromise
    expect(store.loading).toBe(false)
  })

  it('sets error state on fetch failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Internal Server Error', status: 500 })
    mockApi.get.mockRejectedValue(apiError)
    const store = useMoneyWastedStore()

    await expect(store.fetchAll()).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.error!.status).toBe(500)
    expect(store.loading).toBe(false)
  })

  it('clears previous error on successful fetch', async () => {
    const store = useMoneyWastedStore()
    store.error = new ApiError({ message: 'old error', detail: 'old' }) as typeof store.error

    mockApi.get.mockResolvedValue({ data: [] })
    await store.fetchAll()
    expect(store.error).toBeNull()
  })

  // --- create ---

  it('creates a money wasted entry and adds to state', async () => {
    const created = {
      id: 4,
      item: 'Fancy Pen',
      amount: 45.0,
      date_wasted: '2026-03-14',
      notes: 'Lost it immediately',
    }
    mockApi.post.mockResolvedValue({ data: created })
    const store = useMoneyWastedStore()

    const result = await store.create({
      item: 'Fancy Pen',
      amount: 45.0,
      date_wasted: '2026-03-14',
      notes: 'Lost it immediately',
    })

    expect(mockApi.post).toHaveBeenCalledWith('/money-wasted/', {
      item: 'Fancy Pen',
      amount: 45.0,
      date_wasted: '2026-03-14',
      notes: 'Lost it immediately',
    })
    expect(result).toEqual(created)
    expect(store.items).toHaveLength(1)
  })

  it('sets error state on create failure', async () => {
    const apiError = new ApiError({
      message: 'API 422',
      detail: 'Validation error',
      status: 422,
      validationErrors: [{ field: 'amount', message: 'Must be positive' }],
    })
    mockApi.post.mockRejectedValue(apiError)
    const store = useMoneyWastedStore()

    await expect(store.create({ item: 'Bad', amount: -1, date_wasted: '2026-01-01' })).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.items).toEqual([])
  })

  // --- remove ---

  it('removes an item from the list', async () => {
    mockApi.delete.mockResolvedValue({})
    const store = useMoneyWastedStore()
    store.items = [...testItems]

    await store.remove(2)

    expect(mockApi.delete).toHaveBeenCalledWith('/money-wasted/2/')
    expect(store.items).toHaveLength(2)
    expect(store.items.find((i) => i.id === 2)).toBeUndefined()
  })

  it('does not remove on delete failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Database error', status: 500 })
    mockApi.delete.mockRejectedValue(apiError)
    const store = useMoneyWastedStore()
    store.items = [...testItems]

    await expect(store.remove(1)).rejects.toThrow(ApiError)
    expect(store.items).toHaveLength(3)
    expect(store.error!.status).toBe(500)
  })

  // --- sortedItems ---

  it('sorts items by date_wasted descending', () => {
    const store = useMoneyWastedStore()
    store.items = [...testItems]
    const sorted = store.sortedItems
    expect(sorted[0]!.item).toBe('Online Course') // 2026-03-05
    expect(sorted[1]!.item).toBe('Gym Membership') // 2026-02-01
    expect(sorted[2]!.item).toBe('Expensive Blender') // 2026-01-10
  })

  // --- totalWasted ---

  it('computes total amount wasted', () => {
    const store = useMoneyWastedStore()
    store.items = [...testItems]
    expect(store.totalWasted).toBeCloseTo(659.98, 2)
  })

  it('returns 0 for empty list', () => {
    const store = useMoneyWastedStore()
    expect(store.totalWasted).toBe(0)
  })

  // --- clearError ---

  it('clears error state', () => {
    const store = useMoneyWastedStore()
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
    const store = useMoneyWastedStore()

    await expect(store.fetchAll()).rejects.toThrow(ApiError)
    expect(store.error!.isNetworkError).toBe(true)
    expect(store.error!.userMessage).toBe('Unable to reach the server. Check your connection.')
  })
})
