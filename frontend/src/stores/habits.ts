import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import type {
  Habit,
  HabitCreate,
  HabitUpdate,
  HabitCategory,
  HabitCategoryCreate,
  HabitCategoryUpdate,
  HabitCompleted,
  HabitCompletedCreate,
} from '@/api/client'

const logger = createLogger('HabitsStore')

type DateFilter = 'today' | 'yesterday' | 'this_week' | 'last_7' | 'this_month' | 'last_30' | 'this_year' | 'all'

interface DateRange {
  start_date?: string
  end_date?: string
}

function getDateRange(filter: DateFilter): DateRange {
  if (filter === 'all') return {}

  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)

  let start: Date

  switch (filter) {
    case 'today':
      start = today
      break
    case 'yesterday':
      start = new Date(today)
      start.setDate(start.getDate() - 1)
      return { start_date: start.toISOString(), end_date: today.toISOString() }
    case 'this_week': {
      const day = today.getDay()
      const diff = day === 0 ? 6 : day - 1
      start = new Date(today)
      start.setDate(start.getDate() - diff)
      const weekEnd = new Date(start)
      weekEnd.setDate(weekEnd.getDate() + 7)
      return { start_date: start.toISOString(), end_date: weekEnd.toISOString() }
    }
    case 'last_7':
      start = new Date(today)
      start.setDate(start.getDate() - 7)
      break
    case 'this_month':
      start = new Date(today.getFullYear(), today.getMonth(), 1)
      return {
        start_date: start.toISOString(),
        end_date: new Date(today.getFullYear(), today.getMonth() + 1, 1).toISOString(),
      }
    case 'last_30':
      start = new Date(today)
      start.setDate(start.getDate() - 30)
      break
    case 'this_year':
      start = new Date(today.getFullYear(), 0, 1)
      return {
        start_date: start.toISOString(),
        end_date: new Date(today.getFullYear() + 1, 0, 1).toISOString(),
      }
  }

  return { start_date: start.toISOString(), end_date: tomorrow.toISOString() }
}

function groupByCategory<T extends { category: HabitCategory }>(items: T[]): Record<string, T[]> {
  const categoryNames = [...new Set(items.map((item) => item.category.name))].sort()
  const importantIdx = categoryNames.indexOf('IMPORTANT')
  if (importantIdx > 0) {
    categoryNames.splice(importantIdx, 1)
    categoryNames.unshift('IMPORTANT')
  }
  const grouped: Record<string, T[]> = {}
  for (const name of categoryNames) {
    grouped[name] = items.filter((item) => item.category.name === name)
  }
  return grouped
}

export const DATE_FILTERS: DateFilter[] = ['today', 'yesterday', 'this_week', 'last_7', 'this_month', 'last_30', 'this_year', 'all']

export type { DateFilter }

export const useHabitsStore = defineStore('habits', () => {
  const habits = ref<Habit[]>([])
  const categories = ref<HabitCategory[]>([])
  const completedHabits = ref<HabitCompleted[]>([])
  const loading = ref(false)
  const error = ref<ApiError | null>(null)
  const selectedFilter = ref<DateFilter>('this_week')

  const currentHabits = computed(() => habits.value.filter((h) => h.is_current))
  const hibernatingHabits = computed(() => habits.value.filter((h) => !h.is_current))
  const currentCategories = computed(() => categories.value.filter((c) => c.is_current))
  const hibernatingCategories = computed(() => categories.value.filter((c) => !c.is_current))

  const habitsByCategory = computed(() => groupByCategory(currentHabits.value))

  const todoHabits = computed(() => {
    const completedNames = new Set(completedHabits.value.map((c) => c.name))
    const todo = currentHabits.value.filter((h) => !completedNames.has(h.name))
    return groupByCategory(todo)
  })

  const doneHabits = computed(() => groupByCategory(completedHabits.value))

  const chartData = computed(() => {
    const completed = completedHabits.value
    if (completed.length === 0) return { labels: [], values: [] }

    const sorted = [...completed].sort((a, b) => new Date(a.complete_date).getTime() - new Date(b.complete_date).getTime())

    const first = new Date(sorted[0]!.complete_date)
    const last = new Date(sorted[sorted.length - 1]!.complete_date)
    const firstDay = new Date(first.getFullYear(), first.getMonth(), first.getDate())
    const lastDay = new Date(last.getFullYear(), last.getMonth(), last.getDate())

    const counts = new Map<string, number>()
    const dayMs = 86400000
    for (let d = firstDay.getTime(); d <= lastDay.getTime(); d += dayMs) {
      const key = new Date(d).toISOString().split('T')[0]!
      counts.set(key, 0)
    }

    for (const habit of sorted) {
      const d = new Date(habit.complete_date)
      const key = new Date(d.getFullYear(), d.getMonth(), d.getDate()).toISOString().split('T')[0]!
      counts.set(key, (counts.get(key) ?? 0) + 1)
    }

    const labels: string[] = []
    const values: number[] = []
    for (const [dateStr, count] of counts) {
      const d = new Date(dateStr + 'T00:00:00')
      labels.push(d.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }))
      values.push(count)
    }

    return { labels, values }
  })

  function clearError() {
    error.value = null
  }

  // --- Habits ---

  async function fetchHabits(params?: Record<string, string | boolean>) {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<Habit[]>('/habits/', { params })
      habits.value = response.data
      logger.info('habits_fetched', { count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('habits_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    } finally {
      loading.value = false
    }
  }

  async function createHabit(input: HabitCreate) {
    error.value = null
    try {
      const response = await api.post<Habit>('/habits/', input)
      habits.value.push(response.data)
      logger.info('habit_created', { id: response.data.id, name: response.data.name })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('habit_create_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function updateHabit(id: number, input: HabitUpdate) {
    error.value = null
    try {
      const response = await api.patch<Habit>(`/habits/${id}/`, input)
      const index = habits.value.findIndex((h) => h.id === id)
      if (index !== -1) {
        habits.value[index] = response.data
      }
      logger.info('habit_updated', { id })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('habit_update_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function deleteHabit(id: number) {
    error.value = null
    try {
      await api.delete(`/habits/${id}/`)
      habits.value = habits.value.filter((h) => h.id !== id)
      logger.info('habit_deleted', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('habit_delete_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function hibernateHabit(id: number) {
    return updateHabit(id, { is_current: false })
  }

  async function reviveHabit(id: number) {
    return updateHabit(id, { is_current: true })
  }

  // --- Categories ---

  async function fetchCategories(params?: Record<string, string | boolean>) {
    error.value = null
    try {
      const response = await api.get<HabitCategory[]>('/habits/categories/', { params })
      categories.value = response.data
      logger.info('categories_fetched', { count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('categories_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function createCategory(input: HabitCategoryCreate) {
    error.value = null
    try {
      const response = await api.post<HabitCategory>('/habits/categories/', input)
      categories.value.push(response.data)
      logger.info('category_created', { id: response.data.id, name: response.data.name })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('category_create_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function updateCategory(id: number, input: HabitCategoryUpdate) {
    error.value = null
    try {
      const response = await api.patch<HabitCategory>(`/habits/categories/${id}/`, input)
      const index = categories.value.findIndex((c) => c.id === id)
      if (index !== -1) {
        categories.value[index] = response.data
      }
      logger.info('category_updated', { id })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('category_update_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function deleteCategory(id: number) {
    error.value = null
    try {
      await api.delete(`/habits/categories/${id}/`)
      categories.value = categories.value.filter((c) => c.id !== id)
      logger.info('category_deleted', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('category_delete_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function hibernateCategory(id: number) {
    return updateCategory(id, { is_current: false })
  }

  async function reviveCategory(id: number) {
    return updateCategory(id, { is_current: true })
  }

  // --- Completed ---

  async function fetchCompleted(params?: Record<string, string>) {
    error.value = null
    try {
      const response = await api.get<HabitCompleted[]>('/habits/completed/', { params })
      completedHabits.value = response.data
      logger.info('completed_fetched', { count: response.data.length })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('completed_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function completeHabit(habit: Habit) {
    error.value = null
    try {
      const payload: HabitCompletedCreate = {
        name: habit.name,
        category_id: habit.category_id,
        complete_date: new Date().toISOString(),
      }
      const response = await api.post<HabitCompleted>('/habits/completed/', payload)
      completedHabits.value.push(response.data)
      logger.info('habit_completed', { id: response.data.id, name: habit.name })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('habit_complete_failed', { name: habit.name, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function deleteCompleted(id: number) {
    error.value = null
    try {
      await api.delete(`/habits/completed/${id}/`)
      completedHabits.value = completedHabits.value.filter((c) => c.id !== id)
      logger.info('completed_deleted', { id })
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('completed_delete_failed', { id, detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  // --- Compound fetchers ---

  async function fetchDailyData() {
    loading.value = true
    error.value = null
    try {
      const today = new Date()
      const todayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate())
      const tomorrow = new Date(todayStart)
      tomorrow.setDate(tomorrow.getDate() + 1)
      const params = {
        start_date: todayStart.toISOString(),
        end_date: tomorrow.toISOString(),
      }
      await Promise.all([fetchHabits({ current: true }), fetchCompleted(params)])
    } catch {
      // errors already set by individual fetchers
    } finally {
      loading.value = false
    }
  }

  async function fetchManageData() {
    loading.value = true
    error.value = null
    try {
      await Promise.all([fetchHabits(), fetchCategories(), fetchCompleted()])
    } catch {
      // errors already set by individual fetchers
    } finally {
      loading.value = false
    }
  }

  async function fetchCompletedFiltered(filter?: DateFilter) {
    const f = filter ?? selectedFilter.value
    selectedFilter.value = f
    const params = getDateRange(f)
    const stringParams: Record<string, string> = {}
    if (params.start_date) stringParams.start_date = params.start_date
    if (params.end_date) stringParams.end_date = params.end_date
    await fetchCompleted(Object.keys(stringParams).length > 0 ? stringParams : undefined)
  }

  return {
    habits,
    categories,
    completedHabits,
    loading,
    error,
    selectedFilter,
    currentHabits,
    hibernatingHabits,
    currentCategories,
    hibernatingCategories,
    habitsByCategory,
    todoHabits,
    doneHabits,
    chartData,
    clearError,
    fetchHabits,
    createHabit,
    updateHabit,
    deleteHabit,
    hibernateHabit,
    reviveHabit,
    fetchCategories,
    createCategory,
    updateCategory,
    deleteCategory,
    hibernateCategory,
    reviveCategory,
    fetchCompleted,
    completeHabit,
    deleteCompleted,
    fetchDailyData,
    fetchManageData,
    fetchCompletedFiltered,
  }
})
