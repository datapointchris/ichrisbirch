import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useDurationsStore } from '../durations'
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

const testDurations = [
  {
    id: 1,
    name: 'Learning Piano',
    start_date: '2023-01-15',
    end_date: null,
    notes: 'Self-taught',
    color: '#4A90D9',
    duration_notes: [
      { id: 1, duration_id: 1, date: '2023-03-01', content: 'Completed beginner course' },
      { id: 2, duration_id: 1, date: '2023-09-10', content: 'Started intermediate' },
    ],
  },
  {
    id: 2,
    name: 'Lived in NC',
    start_date: '2018-06-01',
    end_date: '2022-08-15',
    notes: 'Raleigh',
    color: '#E74C3C',
    duration_notes: [{ id: 3, duration_id: 2, date: '2019-01-01', content: 'Got promoted' }],
  },
  {
    id: 3,
    name: 'Running',
    start_date: '2024-04-01',
    end_date: null,
    notes: null,
    color: null,
    duration_notes: [],
  },
]

describe('useDurationsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  // --- Initial state ---

  it('initializes with empty state', () => {
    const store = useDurationsStore()
    expect(store.durations).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  // --- fetchAll ---

  it('fetches durations from API and sets state', async () => {
    mockApi.get.mockResolvedValue({ data: testDurations })
    const store = useDurationsStore()

    await store.fetchAll()

    expect(mockApi.get).toHaveBeenCalledWith('/durations/')
    expect(store.durations).toEqual(testDurations)
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
    const store = useDurationsStore()

    const fetchPromise = store.fetchAll()
    expect(store.loading).toBe(true)

    resolvePromise({ data: [] })
    await fetchPromise
    expect(store.loading).toBe(false)
  })

  it('sets error state on fetch failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Internal Server Error', status: 500 })
    mockApi.get.mockRejectedValue(apiError)
    const store = useDurationsStore()

    await expect(store.fetchAll()).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.loading).toBe(false)
  })

  // --- create ---

  it('creates a duration and adds it to the list', async () => {
    const newDuration = {
      id: 4,
      name: 'New Hobby',
      start_date: '2025-01-01',
      end_date: null,
      notes: null,
      color: null,
      duration_notes: [],
    }
    mockApi.post.mockResolvedValue({ data: newDuration })
    const store = useDurationsStore()

    const result = await store.create({ name: 'New Hobby', start_date: '2025-01-01' })

    expect(mockApi.post).toHaveBeenCalledWith('/durations/', { name: 'New Hobby', start_date: '2025-01-01' })
    expect(result).toEqual(newDuration)
    expect(store.durations).toContainEqual(newDuration)
  })

  it('sets error state on create failure', async () => {
    const apiError = new ApiError({ message: 'API 422', detail: 'Validation error', status: 422 })
    mockApi.post.mockRejectedValue(apiError)
    const store = useDurationsStore()

    await expect(store.create({ name: 'Bad', start_date: '' })).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.durations).toEqual([])
  })

  // --- update ---

  it('updates a duration in place', async () => {
    const updated = { ...testDurations[0], name: 'Updated Piano' }
    mockApi.patch.mockResolvedValue({ data: updated })
    const store = useDurationsStore()
    store.durations = [...testDurations]

    const result = await store.update(1, { name: 'Updated Piano' })

    expect(mockApi.patch).toHaveBeenCalledWith('/durations/1/', { name: 'Updated Piano' })
    expect(result).toEqual(updated)
    expect(store.durations.find((d) => d.id === 1)!.name).toBe('Updated Piano')
  })

  // --- remove ---

  it('removes a duration from the list', async () => {
    mockApi.delete.mockResolvedValue({})
    const store = useDurationsStore()
    store.durations = [...testDurations]

    await store.remove(2)

    expect(mockApi.delete).toHaveBeenCalledWith('/durations/2/')
    expect(store.durations).toHaveLength(2)
    expect(store.durations.find((d) => d.id === 2)).toBeUndefined()
  })

  it('does not remove on delete failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Database error', status: 500 })
    mockApi.delete.mockRejectedValue(apiError)
    const store = useDurationsStore()
    store.durations = [...testDurations]

    await expect(store.remove(1)).rejects.toThrow(ApiError)
    expect(store.durations).toHaveLength(3)
  })

  // --- sortedDurations ---

  it('sorts durations by start_date ascending', () => {
    const store = useDurationsStore()
    store.durations = [...testDurations]
    const sorted = store.sortedDurations

    expect(sorted[0]!.name).toBe('Lived in NC') // 2018
    expect(sorted[1]!.name).toBe('Learning Piano') // 2023
    expect(sorted[2]!.name).toBe('Running') // 2024
  })

  // --- addNote ---

  it('adds a note to a duration', async () => {
    const newNote = { id: 10, duration_id: 1, date: '2025-06-15', content: 'New milestone' }
    mockApi.post.mockResolvedValue({ data: newNote })
    const store = useDurationsStore()
    store.durations = JSON.parse(JSON.stringify(testDurations))

    const result = await store.addNote(1, { date: '2025-06-15', content: 'New milestone' })

    expect(mockApi.post).toHaveBeenCalledWith('/durations/1/notes/', { date: '2025-06-15', content: 'New milestone' })
    expect(result).toEqual(newNote)
    const duration = store.durations.find((d) => d.id === 1)!
    expect(duration.duration_notes).toContainEqual(newNote)
  })

  // --- updateNote ---

  it('updates a note in a duration', async () => {
    const updatedNote = { id: 1, duration_id: 1, date: '2023-03-01', content: 'Updated content' }
    mockApi.patch.mockResolvedValue({ data: updatedNote })
    const store = useDurationsStore()
    store.durations = JSON.parse(JSON.stringify(testDurations))

    const result = await store.updateNote(1, 1, { content: 'Updated content' })

    expect(mockApi.patch).toHaveBeenCalledWith('/durations/1/notes/1/', { content: 'Updated content' })
    expect(result).toEqual(updatedNote)
    const duration = store.durations.find((d) => d.id === 1)!
    expect(duration.duration_notes.find((n) => n.id === 1)!.content).toBe('Updated content')
  })

  // --- removeNote ---

  it('removes a note from a duration', async () => {
    mockApi.delete.mockResolvedValue({})
    const store = useDurationsStore()
    store.durations = JSON.parse(JSON.stringify(testDurations))

    await store.removeNote(1, 1)

    expect(mockApi.delete).toHaveBeenCalledWith('/durations/1/notes/1/')
    const duration = store.durations.find((d) => d.id === 1)!
    expect(duration.duration_notes.find((n) => n.id === 1)).toBeUndefined()
    expect(duration.duration_notes).toHaveLength(1)
  })

  // --- clearError ---

  it('clears error state', () => {
    const store = useDurationsStore()
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
    const store = useDurationsStore()

    await expect(store.fetchAll()).rejects.toThrow(ApiError)
    expect(store.error!.isNetworkError).toBe(true)
    expect(store.error!.userMessage).toBe('Unable to reach the server. Check your connection.')
  })
})
