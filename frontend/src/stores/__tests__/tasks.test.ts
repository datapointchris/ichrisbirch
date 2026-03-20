import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTasksStore, daysToComplete, timeToComplete } from '../tasks'
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

// Test data with varied priorities to exercise computed filters
const testTasks: Task[] = [
  { id: 1, name: 'Fix leaky faucet', category: 'Home', priority: -2, add_date: '2026-01-01T00:00:00' },
  { id: 2, name: 'Oil change', category: 'Automotive', priority: 0.5, add_date: '2026-02-01T00:00:00' },
  { id: 3, name: 'Buy groceries', category: 'Purchase', priority: 1, add_date: '2026-02-15T00:00:00' },
  { id: 4, name: 'Learn Rust', category: 'Learn', priority: 3, add_date: '2026-03-01T00:00:00', notes: 'Start with the book' },
  { id: 5, name: 'Clean garage', category: 'Chore', priority: 7, add_date: '2026-03-10T00:00:00' },
]

const testCompletedTasks: CompletedTask[] = [
  {
    id: 10,
    name: 'Paint bedroom',
    category: 'Home',
    priority: 5,
    add_date: '2026-01-01T00:00:00',
    complete_date: '2026-01-15T00:00:00',
  },
  {
    id: 11,
    name: 'File taxes',
    category: 'Financial',
    priority: 2,
    add_date: '2026-02-01T00:00:00',
    complete_date: '2026-03-01T00:00:00',
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
    const newTask: Task = { id: 6, name: 'New Task', category: 'Chore', priority: 10, add_date: '2026-03-19T00:00:00' }
    mockApi.post.mockResolvedValue({ data: newTask })
    const store = useTasksStore()

    const result = await store.create({ name: 'New Task', category: 'Chore', priority: 10 })

    expect(mockApi.post).toHaveBeenCalledWith('/tasks/', { name: 'New Task', category: 'Chore', priority: 10 })
    expect(result).toEqual(newTask)
    expect(store.tasks).toContainEqual(newTask)
  })

  it('sets error state on create failure', async () => {
    const apiError = new ApiError({ message: 'API 422', detail: 'Validation error', status: 422 })
    mockApi.post.mockRejectedValue(apiError)
    const store = useTasksStore()

    await expect(store.create({ name: '', category: 'Chore', priority: 1 })).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.tasks).toEqual([])
  })

  // --- complete ---

  it('completes a task and removes it from todo list', async () => {
    const completed: CompletedTask = {
      id: 3,
      name: 'Buy groceries',
      category: 'Purchase',
      priority: 1,
      add_date: '2026-02-15T00:00:00',
      complete_date: '2026-03-19T00:00:00',
    }
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

  // --- extend ---

  it('extends a task and updates it in place', async () => {
    const extended: Task = { ...testTasks[2]!, priority: 8 }
    mockApi.patch.mockResolvedValue({ data: extended })
    const store = useTasksStore()
    store.tasks = [...testTasks]

    await store.extend(3, 7)

    expect(mockApi.patch).toHaveBeenCalledWith('/tasks/3/extend/7/')
    expect(store.tasks.find((t) => t.id === 3)!.priority).toBe(8)
  })

  it('sets error on extend failure', async () => {
    const apiError = new ApiError({ message: 'API 404', detail: 'Task not found', status: 404 })
    mockApi.patch.mockRejectedValue(apiError)
    const store = useTasksStore()

    await expect(store.extend(999, 7)).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
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

  // --- resetPriorities ---

  it('calls reset priorities endpoint', async () => {
    mockApi.post.mockResolvedValue({ data: { message: 'Priorities reset successfully' } })
    const store = useTasksStore()

    const message = await store.resetPriorities()

    expect(mockApi.post).toHaveBeenCalledWith('/tasks/reset-priorities/')
    expect(message).toBe('Priorities reset successfully')
  })

  it('sets error on resetPriorities failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Reset failed', status: 500 })
    mockApi.post.mockRejectedValue(apiError)
    const store = useTasksStore()

    await expect(store.resetPriorities()).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
  })

  // --- sortedTasks ---

  it('sorts tasks by priority ascending', () => {
    const store = useTasksStore()
    store.tasks = [...testTasks]

    const priorities = store.sortedTasks.map((t) => t.priority)
    expect(priorities).toEqual([-2, 0.5, 1, 3, 7])
  })

  // --- priority computed counts ---

  it('computes overdueCount for tasks with priority < 1', () => {
    const store = useTasksStore()
    store.tasks = [...testTasks]

    // priority -2 and 0.5 are both < 1
    expect(store.overdueCount).toBe(2)
  })

  it('computes criticalCount for tasks with priority > 0 and <= 2', () => {
    const store = useTasksStore()
    store.tasks = [...testTasks]

    // priority 0.5 and 1 match (> 0 and <= 2)
    expect(store.criticalCount).toBe(2)
  })

  it('computes dueSoonCount for tasks with priority > 2 and <= 5', () => {
    const store = useTasksStore()
    store.tasks = [...testTasks]

    // priority 3 matches (> 2 and <= 5)
    expect(store.dueSoonCount).toBe(1)
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

// --- Exported utility functions ---

describe('daysToComplete', () => {
  it('calculates days between add and complete dates', () => {
    const task: CompletedTask = {
      id: 1,
      name: 'Test',
      category: 'Chore',
      priority: 1,
      add_date: '2026-01-01T00:00:00',
      complete_date: '2026-01-15T00:00:00',
    }
    expect(daysToComplete(task)).toBe(14)
  })

  it('returns minimum of 1 day for same-day completion', () => {
    const task: CompletedTask = {
      id: 1,
      name: 'Test',
      category: 'Chore',
      priority: 1,
      add_date: '2026-03-19T00:00:00',
      complete_date: '2026-03-19T00:00:00',
    }
    expect(daysToComplete(task)).toBe(1)
  })
})

describe('timeToComplete', () => {
  it('formats days as weeks and remainder', () => {
    const task: CompletedTask = {
      id: 1,
      name: 'Test',
      category: 'Chore',
      priority: 1,
      add_date: '2026-02-01T00:00:00',
      complete_date: '2026-03-01T00:00:00',
    }
    // 28 days = 4 weeks, 0 days
    expect(timeToComplete(task)).toBe('4 weeks, 0 days')
  })

  it('handles partial weeks', () => {
    const task: CompletedTask = {
      id: 1,
      name: 'Test',
      category: 'Chore',
      priority: 1,
      add_date: '2026-01-01T00:00:00',
      complete_date: '2026-01-12T00:00:00',
    }
    // 11 days = 1 week, 4 days
    expect(timeToComplete(task)).toBe('1 weeks, 4 days')
  })
})
