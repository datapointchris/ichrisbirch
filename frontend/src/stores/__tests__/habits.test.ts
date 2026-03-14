import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useHabitsStore } from '../habits'
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

const testCategory = { id: 1, name: 'Health', is_current: true }
const testCategoryImportant = { id: 2, name: 'IMPORTANT', is_current: true }
const testCategoryHibernating = { id: 3, name: 'Fitness', is_current: false }

const testHabits = [
  { id: 1, name: 'Meditate', category_id: 1, category: testCategory, is_current: true },
  { id: 2, name: 'Read', category_id: 2, category: testCategoryImportant, is_current: true },
  { id: 3, name: 'Run', category_id: 3, category: testCategoryHibernating, is_current: false },
]

const testCompleted = [
  { id: 10, name: 'Meditate', category_id: 1, category: testCategory, complete_date: '2026-03-14T08:00:00Z' },
  { id: 11, name: 'Read', category_id: 2, category: testCategoryImportant, complete_date: '2026-03-14T09:00:00Z' },
  { id: 12, name: 'Meditate', category_id: 1, category: testCategory, complete_date: '2026-03-13T08:00:00Z' },
]

describe('useHabitsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  // --- Initial state ---

  it('initializes with empty state', () => {
    const store = useHabitsStore()
    expect(store.habits).toEqual([])
    expect(store.categories).toEqual([])
    expect(store.completedHabits).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
    expect(store.selectedFilter).toBe('this_week')
  })

  // --- fetchHabits ---

  it('fetches habits from API', async () => {
    mockApi.get.mockResolvedValue({ data: testHabits })
    const store = useHabitsStore()

    await store.fetchHabits()

    expect(mockApi.get).toHaveBeenCalledWith('/habits/', { params: undefined })
    expect(store.habits).toEqual(testHabits)
    expect(store.loading).toBe(false)
  })

  it('fetches habits with params', async () => {
    mockApi.get.mockResolvedValue({ data: [testHabits[0], testHabits[1]] })
    const store = useHabitsStore()

    await store.fetchHabits({ current: true })

    expect(mockApi.get).toHaveBeenCalledWith('/habits/', { params: { current: true } })
  })

  it('sets error on fetch habits failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Server error', status: 500 })
    mockApi.get.mockRejectedValue(apiError)
    const store = useHabitsStore()

    await expect(store.fetchHabits()).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
    expect(store.loading).toBe(false)
  })

  // --- fetchCategories ---

  it('fetches categories from API', async () => {
    const categories = [testCategory, testCategoryImportant]
    mockApi.get.mockResolvedValue({ data: categories })
    const store = useHabitsStore()

    await store.fetchCategories()

    expect(mockApi.get).toHaveBeenCalledWith('/habits/categories/', { params: undefined })
    expect(store.categories).toEqual(categories)
  })

  // --- fetchCompleted ---

  it('fetches completed habits', async () => {
    mockApi.get.mockResolvedValue({ data: testCompleted })
    const store = useHabitsStore()

    await store.fetchCompleted({ start_date: '2026-03-13', end_date: '2026-03-15' })

    expect(mockApi.get).toHaveBeenCalledWith('/habits/completed/', {
      params: { start_date: '2026-03-13', end_date: '2026-03-15' },
    })
    expect(store.completedHabits).toEqual(testCompleted)
  })

  // --- createHabit ---

  it('creates a habit and adds to state', async () => {
    const created = { id: 4, name: 'Yoga', category_id: 1, category: testCategory, is_current: true }
    mockApi.post.mockResolvedValue({ data: created })
    const store = useHabitsStore()

    const result = await store.createHabit({ name: 'Yoga', category_id: 1 })

    expect(mockApi.post).toHaveBeenCalledWith('/habits/', { name: 'Yoga', category_id: 1 })
    expect(result).toEqual(created)
    expect(store.habits).toHaveLength(1)
  })

  it('sets error on create habit failure', async () => {
    const apiError = new ApiError({ message: 'API 422', detail: 'Validation error', status: 422 })
    mockApi.post.mockRejectedValue(apiError)
    const store = useHabitsStore()

    await expect(store.createHabit({ name: 'X', category_id: 1 })).rejects.toThrow(ApiError)
    expect(store.error).toBe(apiError)
  })

  // --- updateHabit ---

  it('updates a habit in place', async () => {
    const updated = { ...testHabits[0]!, name: 'Deep Meditate' }
    mockApi.patch.mockResolvedValue({ data: updated })
    const store = useHabitsStore()
    store.habits = [...testHabits]

    await store.updateHabit(1, { name: 'Deep Meditate' })

    expect(mockApi.patch).toHaveBeenCalledWith('/habits/1/', { name: 'Deep Meditate' })
    expect(store.habits.find((h) => h.id === 1)!.name).toBe('Deep Meditate')
  })

  // --- deleteHabit ---

  it('deletes a habit from state', async () => {
    mockApi.delete.mockResolvedValue({})
    const store = useHabitsStore()
    store.habits = [...testHabits]

    await store.deleteHabit(1)

    expect(mockApi.delete).toHaveBeenCalledWith('/habits/1/')
    expect(store.habits.find((h) => h.id === 1)).toBeUndefined()
  })

  it('does not remove habit on delete failure', async () => {
    const apiError = new ApiError({ message: 'API 500', detail: 'Error', status: 500 })
    mockApi.delete.mockRejectedValue(apiError)
    const store = useHabitsStore()
    store.habits = [...testHabits]

    await expect(store.deleteHabit(1)).rejects.toThrow(ApiError)
    expect(store.habits).toHaveLength(3)
  })

  // --- hibernateHabit / reviveHabit ---

  it('hibernates a habit by patching is_current to false', async () => {
    const updated = { ...testHabits[0]!, is_current: false }
    mockApi.patch.mockResolvedValue({ data: updated })
    const store = useHabitsStore()
    store.habits = [...testHabits]

    await store.hibernateHabit(1)

    expect(mockApi.patch).toHaveBeenCalledWith('/habits/1/', { is_current: false })
  })

  it('revives a habit by patching is_current to true', async () => {
    const updated = { ...testHabits[2]!, is_current: true }
    mockApi.patch.mockResolvedValue({ data: updated })
    const store = useHabitsStore()
    store.habits = [...testHabits]

    await store.reviveHabit(3)

    expect(mockApi.patch).toHaveBeenCalledWith('/habits/3/', { is_current: true })
  })

  // --- createCategory ---

  it('creates a category and adds to state', async () => {
    const created = { id: 4, name: 'Productivity', is_current: true }
    mockApi.post.mockResolvedValue({ data: created })
    const store = useHabitsStore()

    const result = await store.createCategory({ name: 'Productivity' })

    expect(mockApi.post).toHaveBeenCalledWith('/habits/categories/', { name: 'Productivity' })
    expect(result).toEqual(created)
    expect(store.categories).toHaveLength(1)
  })

  // --- updateCategory ---

  it('updates a category in place', async () => {
    const updated = { ...testCategory, name: 'Wellness' }
    mockApi.patch.mockResolvedValue({ data: updated })
    const store = useHabitsStore()
    store.categories = [testCategory, testCategoryImportant]

    await store.updateCategory(1, { name: 'Wellness' })

    expect(mockApi.patch).toHaveBeenCalledWith('/habits/categories/1/', { name: 'Wellness' })
    expect(store.categories.find((c) => c.id === 1)!.name).toBe('Wellness')
  })

  // --- deleteCategory ---

  it('deletes a category from state', async () => {
    mockApi.delete.mockResolvedValue({})
    const store = useHabitsStore()
    store.categories = [testCategory, testCategoryImportant]

    await store.deleteCategory(1)

    expect(mockApi.delete).toHaveBeenCalledWith('/habits/categories/1/')
    expect(store.categories.find((c) => c.id === 1)).toBeUndefined()
  })

  it('handles category delete conflict error', async () => {
    const apiError = new ApiError({ message: 'Conflict', detail: 'Category in use', status: 409 })
    mockApi.delete.mockRejectedValue(apiError)
    const store = useHabitsStore()
    store.categories = [testCategory]

    await expect(store.deleteCategory(1)).rejects.toThrow(ApiError)
    expect(store.error!.status).toBe(409)
    expect(store.categories).toHaveLength(1)
  })

  // --- hibernateCategory / reviveCategory ---

  it('hibernates a category', async () => {
    const updated = { ...testCategory, is_current: false }
    mockApi.patch.mockResolvedValue({ data: updated })
    const store = useHabitsStore()
    store.categories = [testCategory]

    await store.hibernateCategory(1)

    expect(mockApi.patch).toHaveBeenCalledWith('/habits/categories/1/', { is_current: false })
  })

  it('revives a category', async () => {
    const updated = { ...testCategoryHibernating, is_current: true }
    mockApi.patch.mockResolvedValue({ data: updated })
    const store = useHabitsStore()
    store.categories = [testCategoryHibernating]

    await store.reviveCategory(3)

    expect(mockApi.patch).toHaveBeenCalledWith('/habits/categories/3/', { is_current: true })
  })

  // --- completeHabit ---

  it('completes a habit and adds to completedHabits', async () => {
    const completed = {
      id: 20,
      name: 'Meditate',
      category_id: 1,
      category: testCategory,
      complete_date: '2026-03-14T12:00:00Z',
    }
    mockApi.post.mockResolvedValue({ data: completed })
    const store = useHabitsStore()

    const result = await store.completeHabit(testHabits[0]!)

    expect(mockApi.post).toHaveBeenCalledWith(
      '/habits/completed/',
      expect.objectContaining({
        name: 'Meditate',
        category_id: 1,
      })
    )
    expect(result).toEqual(completed)
    expect(store.completedHabits).toHaveLength(1)
  })

  // --- deleteCompleted ---

  it('deletes a completed habit entry', async () => {
    mockApi.delete.mockResolvedValue({})
    const store = useHabitsStore()
    store.completedHabits = [...testCompleted]

    await store.deleteCompleted(10)

    expect(mockApi.delete).toHaveBeenCalledWith('/habits/completed/10/')
    expect(store.completedHabits.find((c) => c.id === 10)).toBeUndefined()
  })

  // --- Computed: currentHabits / hibernatingHabits ---

  it('filters current and hibernating habits', () => {
    const store = useHabitsStore()
    store.habits = [...testHabits]

    expect(store.currentHabits).toHaveLength(2)
    expect(store.hibernatingHabits).toHaveLength(1)
    expect(store.hibernatingHabits[0]!.name).toBe('Run')
  })

  // --- Computed: currentCategories / hibernatingCategories ---

  it('filters current and hibernating categories', () => {
    const store = useHabitsStore()
    store.categories = [testCategory, testCategoryImportant, testCategoryHibernating]

    expect(store.currentCategories).toHaveLength(2)
    expect(store.hibernatingCategories).toHaveLength(1)
    expect(store.hibernatingCategories[0]!.name).toBe('Fitness')
  })

  // --- Computed: habitsByCategory ---

  it('groups current habits by category with IMPORTANT first', () => {
    const store = useHabitsStore()
    store.habits = [...testHabits]

    const grouped = store.habitsByCategory
    const keys = Object.keys(grouped)
    expect(keys[0]).toBe('IMPORTANT')
    expect(keys).toContain('Health')
    expect(grouped['IMPORTANT']).toHaveLength(1)
    expect(grouped['Health']).toHaveLength(1)
  })

  // --- Computed: todoHabits ---

  it('excludes completed habit names from todo list', () => {
    const store = useHabitsStore()
    store.habits = [...testHabits]
    store.completedHabits = [testCompleted[0]!] // Meditate is completed

    const todo = store.todoHabits
    const allTodoNames = Object.values(todo)
      .flat()
      .map((h) => h.name)
    expect(allTodoNames).not.toContain('Meditate')
    expect(allTodoNames).toContain('Read')
  })

  // --- Computed: chartData ---

  it('generates chart data with zero-fill for missing dates', () => {
    const store = useHabitsStore()
    store.completedHabits = [
      { id: 1, name: 'A', category_id: 1, category: testCategory, complete_date: '2026-03-10T08:00:00Z' },
      { id: 2, name: 'B', category_id: 1, category: testCategory, complete_date: '2026-03-10T09:00:00Z' },
      { id: 3, name: 'C', category_id: 1, category: testCategory, complete_date: '2026-03-12T08:00:00Z' },
    ]

    const { labels, values } = store.chartData
    expect(labels).toHaveLength(3) // Mar 10, 11, 12
    expect(values[0]).toBe(2) // Mar 10: 2 completions
    expect(values[1]).toBe(0) // Mar 11: zero-filled
    expect(values[2]).toBe(1) // Mar 12: 1 completion
  })

  it('returns empty chart data when no completions', () => {
    const store = useHabitsStore()
    const { labels, values } = store.chartData
    expect(labels).toEqual([])
    expect(values).toEqual([])
  })

  // --- clearError ---

  it('clears error state', () => {
    const store = useHabitsStore()
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
    const store = useHabitsStore()

    await expect(store.fetchHabits()).rejects.toThrow(ApiError)
    expect(store.error!.isNetworkError).toBe(true)
    expect(store.error!.userMessage).toBe('Unable to reach the server. Check your connection.')
  })

  // --- fetchDailyData ---

  it('fetches daily data (current habits + today completed) in parallel', async () => {
    mockApi.get
      .mockResolvedValueOnce({ data: [testHabits[0], testHabits[1]] }) // habits with current=true
      .mockResolvedValueOnce({ data: [testCompleted[0]] }) // today's completed

    const store = useHabitsStore()
    await store.fetchDailyData()

    expect(mockApi.get).toHaveBeenCalledTimes(2)
    expect(store.loading).toBe(false)
  })

  // --- fetchManageData ---

  it('fetches manage data (all habits, categories, completed)', async () => {
    mockApi.get
      .mockResolvedValueOnce({ data: testHabits })
      .mockResolvedValueOnce({ data: [testCategory, testCategoryImportant] })
      .mockResolvedValueOnce({ data: testCompleted })

    const store = useHabitsStore()
    await store.fetchManageData()

    expect(mockApi.get).toHaveBeenCalledTimes(3)
    expect(store.loading).toBe(false)
  })
})
