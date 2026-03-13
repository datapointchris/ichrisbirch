import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useEventsStore } from '../events'
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

// Reusable test data matching the Event interface
const testEvents = [
  {
    id: 1,
    name: 'Concert',
    date: '2026-09-15T19:00:00',
    venue: 'Madison Square Garden',
    url: 'https://example.com/concert',
    cost: 75.0,
    attending: true,
    notes: 'Bring earplugs',
  },
  { id: 2, name: 'Conference', date: '2026-06-01T09:00:00', venue: 'Convention Center', cost: 250.0, attending: false },
  { id: 3, name: 'Birthday Party', date: '2026-12-25T18:00:00', venue: 'Home', cost: 0, attending: true, notes: 'Bring gift' },
]

describe('useEventsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  // --- Initial state ---

  it('initializes with empty state', () => {
    const store = useEventsStore()
    expect(store.events).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  // --- fetchAll ---

  it('fetches events from API and sets state', async () => {
    mockApi.get.mockResolvedValue({ data: testEvents })
    const store = useEventsStore()

    await store.fetchAll()

    expect(mockApi.get).toHaveBeenCalledWith('/events/')
    expect(store.events).toEqual(testEvents)
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
    const store = useEventsStore()

    const fetchPromise = store.fetchAll()
    expect(store.loading).toBe(true)

    resolvePromise({ data: [] })
    await fetchPromise
    expect(store.loading).toBe(false)
  })

  it('sets error state on fetch failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Internal Server Error', status: 500 })
    mockApi.get.mockRejectedValue(apiError)
    const store = useEventsStore()

    await expect(store.fetchAll()).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.error!.status).toBe(500)
    expect(store.loading).toBe(false)
  })

  it('clears previous error on successful fetch', async () => {
    const store = useEventsStore()
    store.error = new ApiError({ message: 'old error', detail: 'old' }) as typeof store.error

    mockApi.get.mockResolvedValue({ data: [] })
    await store.fetchAll()
    expect(store.error).toBeNull()
  })

  // --- create ---

  it('creates an event and adds it to the list', async () => {
    const newEvent = { id: 4, name: 'Workshop', date: '2027-03-10T10:00:00', venue: 'Library', cost: 15.0, attending: false }
    mockApi.post.mockResolvedValue({ data: newEvent })
    const store = useEventsStore()

    const result = await store.create({ name: 'Workshop', date: '2027-03-10T10:00:00', venue: 'Library', cost: 15.0, attending: false })

    expect(mockApi.post).toHaveBeenCalledWith('/events/', {
      name: 'Workshop',
      date: '2027-03-10T10:00:00',
      venue: 'Library',
      cost: 15.0,
      attending: false,
    })
    expect(result).toEqual(newEvent)
    expect(store.events).toContainEqual(newEvent)
  })

  it('sets error state on create failure', async () => {
    const apiError = new ApiError({
      message: 'API 422',
      detail: 'Validation error',
      status: 422,
      validationErrors: [{ field: 'venue', message: 'Field required' }],
    })
    mockApi.post.mockRejectedValue(apiError)
    const store = useEventsStore()

    await expect(store.create({ name: 'Bad', date: '2027-01-01T00:00:00', venue: '', cost: 0, attending: false })).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.error!.validationErrors).toHaveLength(1)
    expect(store.events).toEqual([]) // not added on failure
  })

  // --- update ---

  it('updates an event in place', async () => {
    const updated = {
      id: 1,
      name: 'Updated Concert',
      date: '2026-09-15T19:00:00',
      venue: 'MSG',
      url: 'https://example.com/concert',
      cost: 85.0,
      attending: true,
      notes: 'Bring earplugs',
    }
    mockApi.patch.mockResolvedValue({ data: updated })
    const store = useEventsStore()
    store.events = [...testEvents]

    const result = await store.update(1, { name: 'Updated Concert', venue: 'MSG', cost: 85.0 })

    expect(mockApi.patch).toHaveBeenCalledWith('/events/1/', { name: 'Updated Concert', venue: 'MSG', cost: 85.0 })
    expect(result).toEqual(updated)
    expect(store.events.find((e) => e.id === 1)!.name).toBe('Updated Concert')
  })

  it('sets error state on update failure', async () => {
    const apiError = new ApiError({ message: 'API 404', detail: 'Event not found', status: 404 })
    mockApi.patch.mockRejectedValue(apiError)
    const store = useEventsStore()

    await expect(store.update(999, { name: 'Ghost' })).rejects.toThrow(ApiError)
    expect(store.error!.status).toBe(404)
  })

  // --- remove ---

  it('removes an event from the list', async () => {
    mockApi.delete.mockResolvedValue({})
    const store = useEventsStore()
    store.events = [...testEvents]

    await store.remove(2)

    expect(mockApi.delete).toHaveBeenCalledWith('/events/2/')
    expect(store.events).toHaveLength(2)
    expect(store.events.find((e) => e.id === 2)).toBeUndefined()
  })

  it('does not remove on delete failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Database error', status: 500 })
    mockApi.delete.mockRejectedValue(apiError)
    const store = useEventsStore()
    store.events = [...testEvents]

    await expect(store.remove(1)).rejects.toThrow(ApiError)
    expect(store.events).toHaveLength(3) // unchanged
    expect(store.error!.status).toBe(500)
  })

  // --- toggleAttending ---

  it('toggleAttending sets attending to true', async () => {
    const toggled = { ...testEvents[1], attending: true }
    mockApi.patch.mockResolvedValue({ data: toggled })
    const store = useEventsStore()
    store.events = [...testEvents]

    await store.toggleAttending(2)

    expect(mockApi.patch).toHaveBeenCalledWith('/events/2/', { attending: true })
    expect(store.events.find((e) => e.id === 2)!.attending).toBe(true)
  })

  it('toggleAttending sets attending to false', async () => {
    const toggled = { ...testEvents[0], attending: false }
    mockApi.patch.mockResolvedValue({ data: toggled })
    const store = useEventsStore()
    store.events = [...testEvents]

    await store.toggleAttending(1)

    expect(mockApi.patch).toHaveBeenCalledWith('/events/1/', { attending: false })
    expect(store.events.find((e) => e.id === 1)!.attending).toBe(false)
  })

  it('sets error state on toggleAttending failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Server error', status: 500 })
    mockApi.patch.mockRejectedValue(apiError)
    const store = useEventsStore()
    store.events = [...testEvents]

    await expect(store.toggleAttending(1)).rejects.toThrow(ApiError)
    expect(store.error!.status).toBe(500)
    expect(store.events.find((e) => e.id === 1)!.attending).toBe(true) // unchanged
  })

  // --- sortedEvents ---

  it('sorts events by date ascending', () => {
    const store = useEventsStore()
    store.events = [...testEvents]
    const sorted = store.sortedEvents
    expect(sorted[0]!.name).toBe('Conference') // June
    expect(sorted[1]!.name).toBe('Concert') // September
    expect(sorted[2]!.name).toBe('Birthday Party') // December
  })

  // --- clearError ---

  it('clears error state', () => {
    const store = useEventsStore()
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
    const store = useEventsStore()

    await expect(store.fetchAll()).rejects.toThrow(ApiError)
    expect(store.error!.isNetworkError).toBe(true)
    expect(store.error!.userMessage).toBe('Unable to reach the server. Check your connection.')
  })
})
