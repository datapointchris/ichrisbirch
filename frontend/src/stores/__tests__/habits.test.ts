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

  it('sends habit_id so the completion points back at a live habit', async () => {
    mockApi.post.mockResolvedValue({ data: { ...testCompleted[0]!, habit_id: 1 } })
    const store = useHabitsStore()

    await store.completeHabit(testHabits[0]!)

    expect(mockApi.post).toHaveBeenCalledWith('/habits/completed/', expect.objectContaining({ habit_id: 1 }))
  })

  it('stamps a completion on today with the current moment', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 2, 14, 21, 30))
    mockApi.post.mockResolvedValue({ data: testCompleted[0] })
    const store = useHabitsStore()

    await store.completeHabit(testHabits[0]!, '2026-03-14')

    const payload = mockApi.post.mock.calls[0]![1] as { complete_date: string }
    expect(new Date(payload.complete_date).getHours()).toBe(21)
    vi.useRealTimers()
  })

  it('stamps a backfilled day at local noon, not at the current time', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 2, 14, 21, 30))
    mockApi.post.mockResolvedValue({ data: testCompleted[2] })
    const store = useHabitsStore()

    await store.completeHabit(testHabits[0]!, '2026-03-11')

    const payload = mockApi.post.mock.calls[0]![1] as { complete_date: string }
    const stamped = new Date(payload.complete_date)
    expect(stamped.getFullYear()).toBe(2026)
    expect(stamped.getMonth()).toBe(2)
    expect(stamped.getDate()).toBe(11)
    expect(stamped.getHours()).toBe(12)
    vi.useRealTimers()
  })

  it('completes against the selected day when no day is passed', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 2, 14, 9, 0))
    mockApi.get.mockResolvedValue({ data: [] })
    mockApi.post.mockResolvedValue({ data: testCompleted[2] })
    const store = useHabitsStore()

    await store.selectDay('2026-03-11')
    await store.completeHabit(testHabits[0]!)

    const payload = mockApi.post.mock.calls[0]![1] as { complete_date: string }
    expect(new Date(payload.complete_date).getDate()).toBe(11)
    vi.useRealTimers()
  })

  // --- day selection ---

  it('starts on today', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 2, 14, 9, 0))
    const store = useHabitsStore()
    expect(store.selectedDate).toBe('2026-03-14')
    expect(store.isToday).toBe(true)
    vi.useRealTimers()
  })

  it('fetches only the selected day when stepping back', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 2, 14, 9, 0))
    mockApi.get.mockResolvedValue({ data: [] })
    const store = useHabitsStore()

    await store.stepDay(-1)

    expect(store.selectedDate).toBe('2026-03-13')
    expect(store.isToday).toBe(false)
    const completedCall = mockApi.get.mock.calls.find((c) => c[0] === '/habits/completed/')!
    const params = (completedCall[1] as { params: { start_date: string; end_date: string } }).params
    expect(new Date(params.start_date).getDate()).toBe(13)
    expect(new Date(params.end_date).getDate()).toBe(14)
    vi.useRealTimers()
  })

  it('refuses to move past today and does not fetch', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 2, 14, 9, 0))
    mockApi.get.mockResolvedValue({ data: [] })
    const store = useHabitsStore()

    await store.stepDay(1)
    await store.selectDay('2026-04-01')

    expect(store.selectedDate).toBe('2026-03-14')
    expect(mockApi.get).not.toHaveBeenCalled()
    vi.useRealTimers()
  })

  it('refuses a key that is not a calendar day', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 2, 14, 9, 0))
    mockApi.get.mockResolvedValue({ data: [] })
    const store = useHabitsStore()

    // new Date rolls both of these over rather than rejecting them: day 0 is the
    // previous month's last day, and 2026-02-31 is 3 March.
    await store.selectDay('2026-03-00')
    await store.selectDay('2026-02-31')
    await store.selectDay('not-a-day')

    expect(store.selectedDate).toBe('2026-03-14')
    expect(mockApi.get).not.toHaveBeenCalled()
    vi.useRealTimers()
  })

  it('throws rather than posting when a widened caller passes a future day', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 2, 14, 9, 0))
    const store = useHabitsStore()

    await expect(store.completeHabit(testHabits[0]!, '2099-01-01')).rejects.toThrow(RangeError)
    await expect(store.fetchDailyData('2099-01-01')).rejects.toThrow(RangeError)

    expect(mockApi.post).not.toHaveBeenCalled()
    expect(store.selectedDate).toBe('2026-03-14')
    vi.useRealTimers()
  })

  it('keeps the day and its completions together when two loads overlap', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 2, 14, 9, 0))
    const store = useHabitsStore()

    const rowFor = (day: string) => [{ ...testCompleted[0]!, id: Number(day.slice(-2)), complete_date: `${day}T12:00:00Z` }]
    const pending: Array<(rows: unknown) => void> = []
    mockApi.get.mockImplementation((url: string) => {
      if (url === '/habits/') return Promise.resolve({ data: [] })
      return new Promise((resolve) => pending.push((rows) => resolve({ data: rows })))
    })

    const first = store.selectDay('2026-03-13')
    const second = store.selectDay('2026-03-12')

    // The older request answers last, which is the ordering that used to win.
    pending[1]!(rowFor('2026-03-12'))
    pending[0]!(rowFor('2026-03-13'))
    await Promise.all([first, second])

    expect(store.selectedDate).toBe('2026-03-12')
    expect(store.completedHabits.map((c) => c.complete_date)).toEqual(['2026-03-12T12:00:00Z'])
    vi.useRealTimers()
  })

  it('leaves the day on screen alone when its fetch fails', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 2, 14, 9, 0))
    const store = useHabitsStore()

    mockApi.get.mockResolvedValue({ data: [testCompleted[0]] })
    await store.selectDay('2026-03-13')

    mockApi.get.mockRejectedValue(new ApiError({ message: 'boom', detail: 'boom', status: 500 }))
    await store.selectDay('2026-03-12')

    expect(store.selectedDate).toBe('2026-03-13')
    expect(store.loading).toBe(false)
    vi.useRealTimers()
  })

  it('tracks today across midnight once it is refreshed', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 2, 14, 23, 50))
    const store = useHabitsStore()
    expect(store.isToday).toBe(true)

    vi.setSystemTime(new Date(2026, 2, 15, 0, 10))
    store.refreshToday()

    expect(store.today).toBe('2026-03-15')
    expect(store.isToday).toBe(false)
    vi.useRealTimers()
  })

  it('follows the clock past midnight and stamps the new day', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 2, 14, 23, 50))
    mockApi.get.mockResolvedValue({ data: [] })
    mockApi.post.mockResolvedValue({ data: testCompleted[0] })
    const store = useHabitsStore()
    await store.fetchDailyData()
    expect(store.selectedDate).toBe('2026-03-14')

    vi.setSystemTime(new Date(2026, 2, 15, 0, 10))
    await store.syncToday()
    await store.completeHabit(testHabits[0]!)

    expect(store.selectedDate).toBe('2026-03-15')
    expect(store.isToday).toBe(true)
    const payload = mockApi.post.mock.calls[0]![1] as { complete_date: string }
    const stamped = new Date(payload.complete_date)
    expect(stamped.getDate()).toBe(15)
    expect(stamped.getHours()).toBe(0)
    vi.useRealTimers()
  })

  it('leaves a deliberately chosen earlier day alone at midnight', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 2, 14, 23, 50))
    mockApi.get.mockResolvedValue({ data: [] })
    const store = useHabitsStore()
    await store.selectDay('2026-03-09')

    vi.setSystemTime(new Date(2026, 2, 15, 0, 10))
    await store.syncToday()

    expect(store.selectedDate).toBe('2026-03-09')
    expect(store.today).toBe('2026-03-15')
    vi.useRealTimers()
  })

  it('returns to today from an earlier day', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 2, 14, 9, 0))
    mockApi.get.mockResolvedValue({ data: [] })
    const store = useHabitsStore()

    await store.selectDay('2026-03-09')
    await store.goToToday()

    expect(store.selectedDate).toBe('2026-03-14')
    expect(store.isToday).toBe(true)
    vi.useRealTimers()
  })

  it('steps across a month boundary', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 2, 14, 9, 0))
    mockApi.get.mockResolvedValue({ data: [] })
    const store = useHabitsStore()

    await store.selectDay('2026-03-01')
    await store.stepDay(-1)

    expect(store.selectedDate).toBe('2026-02-28')
    vi.useRealTimers()
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

  it('marks a habit done by habit_id after it has been renamed', () => {
    const store = useHabitsStore()
    store.habits = [{ id: 1, name: 'Meditation', category_id: 1, category: testCategory, is_current: true }]
    // The completion denormalized the old name; only the id still matches.
    store.completedHabits = [
      { id: 10, habit_id: 1, name: 'Meditate', category_id: 1, category: testCategory, complete_date: '2026-03-11T12:00:00Z' },
    ]

    const todoNames = Object.values(store.todoHabits)
      .flat()
      .map((h) => h.name)
    expect(todoNames).not.toContain('Meditation')
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
