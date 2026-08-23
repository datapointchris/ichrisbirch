import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import { formatDate } from '@/composables/formatDate'
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

/** The local calendar day of `d`, as the YYYY-MM-DD key the date controls speak. */
function toDayKey(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function todayKey(): string {
  return toDayKey(new Date())
}

/** The range covering one local day: this day's midnight to the next day's. */
function dayRange(dayKey: string): Record<string, string> {
  const [y, m, d] = dayKey.split('-').map(Number)
  const start = new Date(y!, m! - 1, d!)
  const end = new Date(y!, m! - 1, d! + 1)
  return { start_date: start.toISOString(), end_date: end.toISOString() }
}

// A day key is YYYY-MM-DD naming a real calendar day, no later than today. Throws
// rather than substituting, so a caller can tell "showed your day" from "showed
// another one". `new Date` rolls a bad component over instead of refusing — day 0
// is the previous month's last day, 2026-02-31 is 3 March — so the parsed date is
// compared back against what was asked for.
function assertSelectableDay(dayKey: string, today: string): void {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dayKey)) {
    throw new RangeError(`habit day must be YYYY-MM-DD, got "${dayKey}"`)
  }
  const [y, m, d] = dayKey.split('-').map(Number)
  const parsed = new Date(y!, m! - 1, d!)
  if (parsed.getFullYear() !== y || parsed.getMonth() !== m! - 1 || parsed.getDate() !== d) {
    throw new RangeError(`habit day "${dayKey}" is not a calendar day`)
  }
  if (dayKey > today) {
    throw new RangeError(`habit day "${dayKey}" is after today — a habit cannot be completed ahead of time`)
  }
}

// Completing today records the moment of the click. A day being filled in after the
// fact has no such moment, so it lands at local noon — far enough from either edge
// that the completion still reads as that day under a nearby UTC offset.
function completionTimestamp(dayKey: string, today: string): string {
  if (dayKey === today) return new Date().toISOString()
  const [y, m, d] = dayKey.split('-').map(Number)
  return new Date(y!, m! - 1, d!, 12).toISOString()
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

export { todayKey }

export const useHabitsStore = defineStore('habits', () => {
  const habits = ref<Habit[]>([])
  const categories = ref<HabitCategory[]>([])
  const completedHabits = ref<HabitCompleted[]>([])
  const loading = ref(false)
  const error = ref<ApiError | null>(null)
  const selectedFilter = ref<DateFilter>('this_week')
  const selectedDate = ref<string>(todayKey())

  // The wall clock is not reactive, so today has to be a ref that something
  // refreshes. Left as a plain call it freezes at setup, and a tab open across
  // midnight then reports every control — arrows, picker bound, Today button — as
  // if yesterday were still today.
  const today = ref<string>(todayKey())

  function refreshToday() {
    today.value = todayKey()
  }

  const isToday = computed(() => selectedDate.value === today.value)

  const currentHabits = computed(() => habits.value.filter((h) => h.is_current))
  const hibernatingHabits = computed(() => habits.value.filter((h) => !h.is_current))
  const currentCategories = computed(() => categories.value.filter((c) => c.is_current))
  const hibernatingCategories = computed(() => categories.value.filter((c) => !c.is_current))

  const habitsByCategory = computed(() => groupByCategory(currentHabits.value))

  // A completion denormalizes the name on purpose, so a habit renamed since is not
  // findable by it. habit_id is the identity where the row carries one; the name is
  // the fallback only for rows that do not, which is every completion recorded
  // before the web client started sending the id.
  const todoHabits = computed(() => {
    const completedIds = new Set(completedHabits.value.map((c) => c.habit_id).filter((id): id is number => id !== null && id !== undefined))
    const unlinkedNames = new Set(completedHabits.value.filter((c) => c.habit_id == null).map((c) => c.name))
    const todo = currentHabits.value.filter((h) => !completedIds.has(h.id) && !unlinkedNames.has(h.name))
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
      labels.push(formatDate(dateStr, 'weekdayDate'))
      values.push(count)
    }

    return { labels, values }
  })

  function clearError() {
    error.value = null
  }

  // --- Habits ---

  // loadHabits returns rather than assigns, so a caller racing two requests can
  // decide which answer wins before anything reaches the state.
  async function loadHabits(params?: Record<string, string | boolean>) {
    try {
      const response = await api.get<Habit[]>('/habits/', { params })
      logger.info('habits_fetched', { count: response.data.length })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('habits_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function fetchHabits(params?: Record<string, string | boolean>) {
    loading.value = true
    error.value = null
    try {
      habits.value = await loadHabits(params)
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

  /** The returning counterpart to fetchCompleted, for the same reason as loadHabits. */
  async function loadCompleted(params?: Record<string, string>) {
    try {
      const response = await api.get<HabitCompleted[]>('/habits/completed/', { params })
      logger.info('completed_fetched', { count: response.data.length })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('completed_fetch_failed', { detail: apiError.detail, status: apiError.status })
      throw apiError
    }
  }

  async function fetchCompleted(params?: Record<string, string>) {
    error.value = null
    completedHabits.value = await loadCompleted(params)
  }

  /** Records a completion. Throws a RangeError for a day the CLI would also refuse. */
  async function completeHabit(habit: Habit, dayKey?: string) {
    error.value = null
    refreshToday()
    const day = dayKey ?? selectedDate.value
    assertSelectableDay(day, today.value)
    try {
      const payload: HabitCompletedCreate = {
        habit_id: habit.id,
        name: habit.name,
        category_id: habit.category_id,
        complete_date: completionTimestamp(day, today.value),
      }
      const response = await api.post<HabitCompleted>('/habits/completed/', payload)
      completedHabits.value.push(response.data)
      logger.info('habit_completed', { id: response.data.id, name: habit.name, day })
      return response.data
    } catch (e) {
      const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
      error.value = apiError
      logger.error('habit_complete_failed', { name: habit.name, day, detail: apiError.detail, status: apiError.status })
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

  // Two day loads can be in flight at once — the arrows sit outside the loading
  // block, and the picker emits per keystroke. Without a token the slower response
  // lands last and puts one day's completions under another day's heading.
  let dayRequest = 0

  /**
   * Load one day's habits and completions. Throws a RangeError for a key that is
   * not a calendar day on or before today; the day on screen is left alone.
   */
  async function fetchDailyData(dayKey?: string) {
    refreshToday()
    const day = dayKey ?? selectedDate.value
    assertSelectableDay(day, today.value)

    const token = ++dayRequest
    loading.value = true
    error.value = null
    try {
      const [habitList, completedList] = await Promise.all([loadHabits({ current: true }), loadCompleted(dayRange(day))])
      if (token !== dayRequest) return
      selectedDate.value = day
      habits.value = habitList
      completedHabits.value = completedList
    } catch {
      // errors already set by the loaders; the day on screen does not move
    } finally {
      if (token === dayRequest) loading.value = false
    }
  }

  /**
   * Show a day, ignoring one that is not selectable. The UI cannot offer such a day
   * — the next arrow stops at today and the picker will not open past it — so this
   * is the floor under a caller that bypasses both, and it logs rather than throws
   * because the arrows are wired fire-and-forget from the template.
   */
  async function selectDay(dayKey: string) {
    try {
      await fetchDailyData(dayKey)
    } catch (e) {
      if (!(e instanceof RangeError)) throw e
      logger.warning('habit_day_refused', { requested: dayKey, showing: selectedDate.value, reason: e.message })
    }
  }

  async function stepDay(delta: number) {
    const [y, m, d] = selectedDate.value.split('-').map(Number)
    await selectDay(toDayKey(new Date(y!, m! - 1, d! + delta)))
  }

  async function goToToday() {
    refreshToday()
    await selectDay(today.value)
  }

  /**
   * Follow the clock past midnight. A page sitting on what was today moves to the
   * new today and reloads; a page parked on an earlier day stays where it is, since
   * the reader chose that day deliberately.
   */
  async function syncToday() {
    const next = todayKey()
    if (next === today.value) return
    const wasOnToday = selectedDate.value === today.value
    today.value = next
    logger.info('habit_day_rolled_over', { to: next, followed: wasOnToday })
    if (wasOnToday) await selectDay(next)
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
    selectedDate,
    today,
    isToday,
    refreshToday,
    syncToday,
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
    selectDay,
    stepDay,
    goToToday,
    fetchManageData,
    fetchCompletedFiltered,
  }
})
