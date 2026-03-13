import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAutoTasksStore } from '../autotasks'
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

const testAutoTasks = [
  {
    id: 1,
    name: 'Clean Kitchen',
    category: 'Chore',
    priority: 5,
    notes: 'Deep clean everything',
    frequency: 'Weekly',
    max_concurrent: 2,
    first_run_date: '2026-01-01T01:15:00',
    last_run_date: '2026-03-10T01:15:00',
    run_count: 10,
  },
  {
    id: 2,
    name: 'Backup Photos',
    category: 'Computer',
    priority: 10,
    frequency: 'Monthly',
    max_concurrent: 1,
    first_run_date: '2026-01-15T01:15:00',
    last_run_date: '2026-02-15T01:15:00',
    run_count: 2,
  },
  {
    id: 3,
    name: 'Oil Change',
    category: 'Automotive',
    priority: 8,
    notes: 'Use synthetic oil',
    frequency: 'Quarterly',
    max_concurrent: 2,
    first_run_date: '2025-06-01T01:15:00',
    last_run_date: '2026-03-13T01:15:00',
    run_count: 4,
  },
]

describe('useAutoTasksStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  // --- Initial state ---

  it('initializes with empty state', () => {
    const store = useAutoTasksStore()
    expect(store.autotasks).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  // --- fetchAll ---

  it('fetches autotasks from API and sets state', async () => {
    mockApi.get.mockResolvedValue({ data: testAutoTasks })
    const store = useAutoTasksStore()

    await store.fetchAll()

    expect(mockApi.get).toHaveBeenCalledWith('/autotasks/')
    expect(store.autotasks).toEqual(testAutoTasks)
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
    const store = useAutoTasksStore()

    const fetchPromise = store.fetchAll()
    expect(store.loading).toBe(true)

    resolvePromise({ data: [] })
    await fetchPromise
    expect(store.loading).toBe(false)
  })

  it('sets error state on fetch failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Internal Server Error', status: 500 })
    mockApi.get.mockRejectedValue(apiError)
    const store = useAutoTasksStore()

    await expect(store.fetchAll()).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.error!.status).toBe(500)
    expect(store.loading).toBe(false)
  })

  it('clears previous error on successful fetch', async () => {
    const store = useAutoTasksStore()
    store.error = new ApiError({ message: 'old error', detail: 'old' }) as typeof store.error

    mockApi.get.mockResolvedValue({ data: [] })
    await store.fetchAll()
    expect(store.error).toBeNull()
  })

  // --- create ---

  it('creates an autotask and runs it immediately', async () => {
    const created = {
      id: 4,
      name: 'Water Plants',
      category: 'Home',
      priority: 3,
      frequency: 'Daily',
      max_concurrent: 2,
      first_run_date: '2026-03-13T12:00:00',
      last_run_date: '2026-03-13T12:00:00',
      run_count: 0,
    }
    const afterRun = { ...created, last_run_date: '2026-03-13T12:00:01', run_count: 1 }
    mockApi.post.mockResolvedValue({ data: created })
    mockApi.patch.mockResolvedValue({ data: afterRun })
    const store = useAutoTasksStore()

    const result = await store.create({
      name: 'Water Plants',
      category: 'Home',
      priority: 3,
      frequency: 'Daily',
    })

    expect(mockApi.post).toHaveBeenCalledWith('/autotasks/', {
      name: 'Water Plants',
      category: 'Home',
      priority: 3,
      frequency: 'Daily',
    })
    expect(mockApi.patch).toHaveBeenCalledWith('/autotasks/4/run/')
    expect(result).toEqual(afterRun)
    expect(store.autotasks).toHaveLength(1)
    expect(store.autotasks[0]!.run_count).toBe(1)
  })

  it('sets error state on create POST failure', async () => {
    const apiError = new ApiError({
      message: 'API 422',
      detail: 'Validation error',
      status: 422,
      validationErrors: [{ field: 'name', message: 'Field required' }],
    })
    mockApi.post.mockRejectedValue(apiError)
    const store = useAutoTasksStore()

    await expect(store.create({ name: '', category: 'Chore', priority: 1, frequency: 'Daily' })).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.autotasks).toEqual([])
    expect(mockApi.patch).not.toHaveBeenCalled()
  })

  it('sets error state when run fails after successful create', async () => {
    const created = {
      id: 5,
      name: 'Failing Task',
      category: 'Chore',
      priority: 1,
      frequency: 'Daily',
      max_concurrent: 2,
      first_run_date: '2026-03-13T12:00:00',
      last_run_date: '2026-03-13T12:00:00',
      run_count: 0,
    }
    const runError = new ApiError({ message: 'API 500', detail: 'Run failed', status: 500 })
    mockApi.post.mockResolvedValue({ data: created })
    mockApi.patch.mockRejectedValue(runError)
    const store = useAutoTasksStore()

    await expect(store.create({ name: 'Failing Task', category: 'Chore', priority: 1, frequency: 'Daily' })).rejects.toThrow(ApiError)
    // Item was added by POST but run failed
    expect(store.autotasks).toHaveLength(1)
    expect(store.autotasks[0]!.run_count).toBe(0)
    expect(store.error).toBe(runError)
  })

  // --- run ---

  it('runs an autotask and updates it in place', async () => {
    const afterRun = { ...testAutoTasks[0], last_run_date: '2026-03-13T01:15:00', run_count: 11 }
    mockApi.patch.mockResolvedValue({ data: afterRun })
    const store = useAutoTasksStore()
    store.autotasks = [...testAutoTasks]

    const result = await store.run(1)

    expect(mockApi.patch).toHaveBeenCalledWith('/autotasks/1/run/')
    expect(result).toEqual(afterRun)
    expect(store.autotasks.find((a) => a.id === 1)!.run_count).toBe(11)
  })

  it('sets error state on run failure', async () => {
    const apiError = new ApiError({ message: 'API 404', detail: 'AutoTask not found', status: 404 })
    mockApi.patch.mockRejectedValue(apiError)
    const store = useAutoTasksStore()
    store.autotasks = [...testAutoTasks]

    await expect(store.run(999)).rejects.toThrow(ApiError)
    expect(store.error!.status).toBe(404)
    // Original data unchanged
    expect(store.autotasks.find((a) => a.id === 1)!.run_count).toBe(10)
  })

  // --- remove ---

  it('removes an autotask from the list', async () => {
    mockApi.delete.mockResolvedValue({})
    const store = useAutoTasksStore()
    store.autotasks = [...testAutoTasks]

    await store.remove(2)

    expect(mockApi.delete).toHaveBeenCalledWith('/autotasks/2/')
    expect(store.autotasks).toHaveLength(2)
    expect(store.autotasks.find((a) => a.id === 2)).toBeUndefined()
  })

  it('does not remove on delete failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Database error', status: 500 })
    mockApi.delete.mockRejectedValue(apiError)
    const store = useAutoTasksStore()
    store.autotasks = [...testAutoTasks]

    await expect(store.remove(1)).rejects.toThrow(ApiError)
    expect(store.autotasks).toHaveLength(3)
    expect(store.error!.status).toBe(500)
  })

  // --- sortedAutoTasks ---

  it('sorts autotasks by last_run_date descending', () => {
    const store = useAutoTasksStore()
    store.autotasks = [...testAutoTasks]
    const sorted = store.sortedAutoTasks
    expect(sorted[0]!.name).toBe('Oil Change') // 2026-03-13
    expect(sorted[1]!.name).toBe('Clean Kitchen') // 2026-03-10
    expect(sorted[2]!.name).toBe('Backup Photos') // 2026-02-15
  })

  // --- clearError ---

  it('clears error state', () => {
    const store = useAutoTasksStore()
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
    const store = useAutoTasksStore()

    await expect(store.fetchAll()).rejects.toThrow(ApiError)
    expect(store.error!.isNetworkError).toBe(true)
    expect(store.error!.userMessage).toBe('Unable to reach the server. Check your connection.')
  })
})
