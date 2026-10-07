import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTasksStore } from '../tasks'
import { ApiError } from '@/api/errors'
import type { Task } from '@/api/client'
import type { CompletedTask } from '../tasks'

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

function makeTask(fields: Pick<Task, 'id' | 'name' | 'category' | 'add_date'> & Partial<Task>): Task {
  return { rank_at: '2026-06-01T00:00:00Z', window_days: 30, pinned: false, ...fields }
}

const testTasks: Task[] = [
  makeTask({ id: 1, name: 'Fix leaky faucet', category: 'Home', add_date: '2026-01-01T00:00:00Z', rank_at: '2026-03-02T00:00:00Z' }),
  makeTask({ id: 2, name: 'Oil change', category: 'Automotive', add_date: '2026-02-01T00:00:00Z', rank_at: '2026-03-18T00:00:00Z' }),
  makeTask({ id: 3, name: 'Buy groceries', category: 'Purchase', add_date: '2026-02-15T00:00:00Z', rank_at: '2026-03-17T00:00:00Z' }),
  makeTask({ id: 4, name: 'Learn Rust', category: 'Learn', add_date: '2026-03-01T00:00:00Z', notes: 'Start with the book' }),
  makeTask({ id: 5, name: 'Clean garage', category: 'Chore', add_date: '2026-03-10T00:00:00Z', rank_at: '2026-04-09T00:00:00Z' }),
]

const testCompletedTasks: CompletedTask[] = [
  {
    ...makeTask({ id: 10, name: 'Paint bedroom', category: 'Home', add_date: '2026-01-01T00:00:00Z' }),
    complete_date: '2026-01-15T00:00:00Z',
  },
  {
    ...makeTask({ id: 11, name: 'File taxes', category: 'Financial', add_date: '2026-02-01T00:00:00Z' }),
    complete_date: '2026-03-01T00:00:00Z',
  },
]

describe('useTasksStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  // --- Initial state ---

  it('initializes with empty state', () => {
    const store = useTasksStore()
    expect(store.tasks).toEqual([])
    expect(store.completedTasks).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  // --- fetchTodo ---

  it('fetches todo tasks from API', async () => {
    mockApi.get.mockResolvedValue({ data: testTasks })
    const store = useTasksStore()

    await store.fetchTodo()

    expect(mockApi.get).toHaveBeenCalledWith('/tasks/todo/')
    expect(store.tasks).toEqual(testTasks)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('sets loading state during fetchTodo', async () => {
    let resolvePromise!: (value: unknown) => void
    mockApi.get.mockReturnValue(
      new Promise((resolve) => {
        resolvePromise = resolve
      })
    )
    const store = useTasksStore()

    const fetchPromise = store.fetchTodo()
    expect(store.loading).toBe(true)

    resolvePromise({ data: [] })
    await fetchPromise
    expect(store.loading).toBe(false)
  })

  it('sets error state on fetchTodo failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Internal Server Error', status: 500 })
    mockApi.get.mockRejectedValue(apiError)
    const store = useTasksStore()

    await expect(store.fetchTodo()).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.loading).toBe(false)
  })

  // --- fetchCompleted ---

  it('fetches completed tasks from API', async () => {
    mockApi.get.mockResolvedValue({ data: testCompletedTasks })
    const store = useTasksStore()

    await store.fetchCompleted()

    expect(mockApi.get).toHaveBeenCalledWith('/tasks/completed/', { params: {} })
    expect(store.completedTasks).toEqual(testCompletedTasks)
  })

  it('passes date range params to fetchCompleted', async () => {
    mockApi.get.mockResolvedValue({ data: [] })
    const store = useTasksStore()

    await store.fetchCompleted('2026-01-01', '2026-03-01')

    expect(mockApi.get).toHaveBeenCalledWith('/tasks/completed/', {
      params: { start_date: '2026-01-01', end_date: '2026-03-01' },
    })
  })

  it('sets error state on fetchCompleted failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Database error', status: 500 })
    mockApi.get.mockRejectedValue(apiError)
    const store = useTasksStore()

    await expect(store.fetchCompleted()).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.loading).toBe(false)
  })

  // --- search ---

  it('searches tasks and splits into todo/completed', async () => {
    const mixedResults = [testTasks[0], { ...testCompletedTasks[0] }]
    mockApi.get.mockResolvedValue({ data: mixedResults })
    const store = useTasksStore()

    await store.search('paint')

    expect(mockApi.get).toHaveBeenCalledWith('/tasks/search/', { params: { q: 'paint' } })
    // Task without complete_date goes to tasks
    expect(store.tasks).toHaveLength(1)
    expect(store.tasks[0]!.id).toBe(1)
    // Task with complete_date goes to completedTasks
    expect(store.completedTasks).toHaveLength(1)
    expect(store.completedTasks[0]!.id).toBe(10)
  })

  it('sets error on search failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Search failed', status: 500 })
    mockApi.get.mockRejectedValue(apiError)
    const store = useTasksStore()

    await expect(store.search('bad')).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.loading).toBe(false)
  })

  // --- create ---

  it('creates a task and adds it to the list', async () => {
    const newTask = makeTask({ id: 6, name: 'New Task', category: 'Chore', add_date: '2026-03-19T00:00:00Z', window_days: 10 })
    mockApi.post.mockResolvedValue({ data: newTask })
    const store = useTasksStore()

    const result = await store.create({ name: 'New Task', category: 'Chore', window_days: 10 })

    expect(mockApi.post).toHaveBeenCalledWith('/tasks/', { name: 'New Task', category: 'Chore', window_days: 10 })
    expect(result).toEqual(newTask)
    expect(store.tasks).toContainEqual(newTask)
  })

  it('sets error state on create failure', async () => {
    const apiError = new ApiError({ message: 'API 422', detail: 'Validation error', status: 422 })
    mockApi.post.mockRejectedValue(apiError)
    const store = useTasksStore()

    await expect(store.create({ name: '', category: 'Chore' })).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.tasks).toEqual([])
  })

  // --- complete ---

  it('completes a task and removes it from todo list', async () => {
    const completed: CompletedTask = { ...testTasks[2]!, complete_date: '2026-03-19T00:00:00Z' }
    mockApi.patch.mockResolvedValue({ data: completed })
    const store = useTasksStore()
    store.tasks = [...testTasks]

    const result = await store.complete(3)

    expect(mockApi.patch).toHaveBeenCalledWith('/tasks/3/complete/')
    expect(result).toEqual(completed)
    expect(store.tasks.find((t) => t.id === 3)).toBeUndefined()
    expect(store.tasks).toHaveLength(4)
  })

  it('sets error on complete failure', async () => {
    const apiError = new ApiError({ message: 'API 404', detail: 'Task not found', status: 404 })
    mockApi.patch.mockRejectedValue(apiError)
    const store = useTasksStore()
    store.tasks = [...testTasks]

    await expect(store.complete(999)).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.tasks).toHaveLength(5) // unchanged
  })

  // --- snooze ---

  it('snoozes a task and replaces it with the server copy', async () => {
    const snoozed: Task = { ...testTasks[0]!, rank_at: '2026-12-01T00:00:00Z' }
    mockApi.patch.mockResolvedValue({ data: snoozed })
    const store = useTasksStore()
    store.tasks = [...testTasks]

    await store.snooze(1)

    expect(mockApi.patch).toHaveBeenCalledWith('/tasks/1/snooze/')
    expect(store.sortedTasks.at(-1)!.id).toBe(1)
  })

  it('sets error on snooze failure', async () => {
    const apiError = new ApiError({ message: 'API 409', detail: 'Task 1 is already completed', status: 409 })
    mockApi.patch.mockRejectedValue(apiError)
    const store = useTasksStore()

    await expect(store.snooze(1)).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
  })

  // --- drop ---

  it('drops a task with a reason and removes it from the list', async () => {
    mockApi.patch.mockResolvedValue({ data: { ...testTasks[1]!, drop_date: '2026-03-19T00:00:00Z' } })
    const store = useTasksStore()
    store.tasks = [...testTasks]

    await store.drop(2, 'Sold the car')

    expect(mockApi.patch).toHaveBeenCalledWith('/tasks/2/drop/', { reason: 'Sold the car' })
    expect(store.tasks.find((t) => t.id === 2)).toBeUndefined()
  })

  it('drops a task without a body when no reason is given', async () => {
    mockApi.patch.mockResolvedValue({ data: testTasks[1] })
    const store = useTasksStore()
    store.tasks = [...testTasks]

    await store.drop(2)

    expect(mockApi.patch).toHaveBeenCalledWith('/tasks/2/drop/', undefined)
  })

  it('keeps the task on drop failure', async () => {
    mockApi.patch.mockRejectedValue(new ApiError({ message: 'API 500', detail: 'boom', status: 500 }))
    const store = useTasksStore()
    store.tasks = [...testTasks]

    await expect(store.drop(2)).rejects.toThrow(ApiError)
    expect(store.tasks).toHaveLength(5)
  })

  // --- remove ---

  it('removes a task from both todo and completed lists', async () => {
    mockApi.delete.mockResolvedValue({})
    const store = useTasksStore()
    store.tasks = [...testTasks]
    store.completedTasks = [...testCompletedTasks]

    await store.remove(2)

    expect(mockApi.delete).toHaveBeenCalledWith('/tasks/2/')
    expect(store.tasks.find((t) => t.id === 2)).toBeUndefined()
    expect(store.tasks).toHaveLength(4)
  })

  it('removes a completed task', async () => {
    mockApi.delete.mockResolvedValue({})
    const store = useTasksStore()
    store.completedTasks = [...testCompletedTasks]

    await store.remove(10)

    expect(store.completedTasks.find((t) => t.id === 10)).toBeUndefined()
    expect(store.completedTasks).toHaveLength(1)
  })

  it('does not remove on delete failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Database error', status: 500 })
    mockApi.delete.mockRejectedValue(apiError)
    const store = useTasksStore()
    store.tasks = [...testTasks]

    await expect(store.remove(1)).rejects.toThrow(ApiError)
    expect(store.tasks).toHaveLength(5)
    expect(store.error!.status).toBe(500)
  })

  // --- pin and move ---

  it('pins a task through a single-row PATCH', async () => {
    mockApi.patch.mockResolvedValue({ data: { ...testTasks[4]!, pinned: true } })
    const store = useTasksStore()
    store.tasks = [...testTasks]

    await store.setPinned(5, true)

    expect(mockApi.patch).toHaveBeenCalledWith('/tasks/5/', { pinned: true })
    expect(store.sortedTasks[0]!.id).toBe(5)
  })

  it('moves a task by sending rank_at, and pinned only when it changes', async () => {
    mockApi.patch.mockResolvedValue({ data: testTasks[0] })
    const store = useTasksStore()
    store.tasks = [...testTasks]

    await store.move(1, '2026-03-20T00:00:00Z')
    expect(mockApi.patch).toHaveBeenLastCalledWith('/tasks/1/', { rank_at: '2026-03-20T00:00:00Z' })

    await store.move(1, '2026-03-20T00:00:00Z', true)
    expect(mockApi.patch).toHaveBeenLastCalledWith('/tasks/1/', { rank_at: '2026-03-20T00:00:00Z', pinned: true })
  })

  it('sets error on update failure', async () => {
    const apiError = new ApiError({ message: 'API 404', detail: 'Task not found', status: 404 })
    mockApi.patch.mockRejectedValue(apiError)
    const store = useTasksStore()

    await expect(store.setPinned(999, true)).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
  })

  // --- sortedTasks ---

  it('sorts pinned first, then by rank_at, then by add_date', () => {
    const store = useTasksStore()
    store.tasks = [
      makeTask({ id: 20, name: 'Newer tie', category: 'Chore', add_date: '2026-03-15T00:00:00Z', rank_at: '2026-04-01T00:00:00Z' }),
      makeTask({ id: 21, name: 'Older tie', category: 'Chore', add_date: '2026-01-01T00:00:00Z', rank_at: '2026-04-01T00:00:00Z' }),
      makeTask({ id: 22, name: 'Earlier rank', category: 'Chore', add_date: '2026-02-01T00:00:00Z', rank_at: '2026-03-01T00:00:00Z' }),
      makeTask({
        id: 23,
        name: 'Pinned, ranked last',
        category: 'Chore',
        add_date: '2026-02-01T00:00:00Z',
        rank_at: '2027-01-01T00:00:00Z',
        pinned: true,
      }),
    ]

    expect(store.sortedTasks.map((t) => t.id)).toEqual([23, 22, 21, 20])
  })

  it('computes totalCount', () => {
    const store = useTasksStore()
    store.tasks = [...testTasks]

    expect(store.totalCount).toBe(5)
  })

  // --- clearError ---

  it('clears error state', () => {
    const store = useTasksStore()
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
    const store = useTasksStore()

    await expect(store.fetchTodo()).rejects.toThrow(ApiError)
    expect(store.error!.isNetworkError).toBe(true)
    expect(store.error!.userMessage).toBe('Unable to reach the server. Check your connection.')
  })
})
