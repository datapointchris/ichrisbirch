import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { ApiError } from '@/api/errors'
import type { Countdown, Event, Habit, HabitCompleted, ShoppingItem, Task, TaskCategory } from '@/api/client'
import { dayKeyOf, daysBetween, todayKey, type DayKey } from '@/composables/calendarDay'
import { dayWindow } from '@/composables/dateFilters'
import { wallClockInstant } from '@/composables/useWallClock'
import { createLogger } from '@/utils/logger'
import { useCountdownsStore } from '@/stores/countdowns'
import { useEventsStore } from '@/stores/events'
import { useHabitsStore } from '@/stores/habits'
import { useShoppingStore } from '@/stores/shopping'
import { type CompletedTask, useTasksStore } from '@/stores/tasks'

const logger = createLogger('TodayStore')

// The page is read on a phone in passing, so it shows the head of each list
// and links to the page holding the rest.
export const OPEN_TASKS_SHOWN = 10
export const COMING_UP_SHOWN = 5

export const TODAY_PARTS = ['tasks', 'habits', 'countdowns', 'events', 'shopping'] as const
export type TodayPart = (typeof TODAY_PARTS)[number]

/** A part shows its rows only once a load of it has landed. */
export type PartStatus = 'loading' | 'loaded' | 'failed'

export interface ComingUpRow {
  kind: 'countdown' | 'event'
  id: number
  name: string
  /** The day it falls on for the reader. */
  day: DayKey
  /** Orders rows within a day. A countdown has no time, so it opens its day. */
  at: number
  attending: boolean
}

function byArrival(a: ComingUpRow, b: ComingUpRow): number {
  if (a.day !== b.day) return a.day < b.day ? -1 : 1
  if (a.at === b.at) return 0
  return a.at < b.at ? -1 : 1
}

/** The countdowns and events still ahead, merged in the order they arrive. */
export function comingUp(countdowns: Countdown[], events: Event[], today: DayKey, now: number = Date.now()): ComingUpRow[] {
  const rows: ComingUpRow[] = countdowns
    .filter((countdown) => countdown.due_date >= today)
    .map((countdown) => ({
      kind: 'countdown',
      id: countdown.id,
      name: countdown.name,
      day: countdown.due_date,
      at: Number.NEGATIVE_INFINITY,
      attending: false,
    }))
  for (const event of events) {
    // How long until an event is a question about the instant, so the venue's
    // wall clock is resolved before its day is read in the reader's zone.
    const at = wallClockInstant(event)
    if (Number.isNaN(at) || at < now) continue
    rows.push({ kind: 'event', id: event.id, name: event.name, day: dayKeyOf(at), at, attending: event.attending })
  }
  return rows.sort(byArrival).slice(0, COMING_UP_SHOWN)
}

/** How far off a day is, in the words a glance reads fastest. */
export function daysUntil(day: DayKey, today: DayKey): string {
  const days = daysBetween(today, day)
  if (days === 0) return 'Today'
  if (days === 1) return 'Tomorrow'
  return `${days} days`
}

function asApiError(e: unknown): ApiError {
  return e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
}

export const useTodayStore = defineStore('today', () => {
  const tasks = useTasksStore()
  const habits = useHabitsStore()
  const countdowns = useCountdownsStore()
  const events = useEventsStore()
  const shopping = useShoppingStore()

  // The habits store owns the day and moves it past midnight, so the page reads
  // its day from there rather than keeping a second one.
  const today = computed(() => habits.today)
  const doneTasks = ref<CompletedTask[]>([])
  const status = ref<Record<TodayPart, PartStatus>>({
    tasks: 'loading',
    habits: 'loading',
    countdowns: 'loading',
    events: 'loading',
    shopping: 'loading',
  })
  const error = ref<ApiError | null>(null)

  const openTasks = computed(() => tasks.sortedTasks.slice(0, OPEN_TASKS_SHOWN))
  const openTaskCount = computed(() => tasks.tasks.length)
  const habitsDue = computed(() => habits.todoHabits)
  const habitsDone = computed(() => habits.dayCompleted)
  const habitsLeft = computed(() => habits.dayDue.length)
  // A part whose last load failed holds rows the page cannot vouch for, so they stay out.
  const comingUpRows = computed(() =>
    comingUp(
      status.value.countdowns === 'loaded' ? countdowns.countdowns : [],
      status.value.events === 'loaded' ? events.events : [],
      today.value
    )
  )
  const shoppingCount = computed(() => shopping.needed.length)

  async function loadTasks(day: DayKey) {
    await tasks.fetchTodo()
    // The tasks store keeps one completed list for every page reading it, so
    // this page takes a copy and leaves the shared one empty, as /tasks does.
    await tasks.fetchCompleted(dayWindow(day))
    doneTasks.value = [...tasks.completedTasks]
    tasks.completedTasks = []
  }

  async function loadHabits(day: DayKey) {
    // The habits store reports a failed day load on its `error` rather than throwing.
    await habits.fetchDailyData(day)
    if (habits.error) throw habits.error
  }

  async function loadEverything(): Promise<TodayPart[]> {
    error.value = null
    habits.refreshToday()
    const day = habits.today
    const loaders: Record<TodayPart, () => Promise<unknown>> = {
      tasks: () => loadTasks(day),
      habits: () => loadHabits(day),
      countdowns: () => countdowns.fetchAll(),
      events: () => events.fetchAll(),
      shopping: () => shopping.fetchAll(),
    }
    const failed: TodayPart[] = []
    await Promise.all(
      TODAY_PARTS.map(async (part) => {
        if (status.value[part] === 'failed') status.value[part] = 'loading'
        try {
          await loaders[part]()
          status.value[part] = 'loaded'
        } catch (e) {
          const apiError = asApiError(e)
          error.value ??= apiError
          status.value[part] = 'failed'
          failed.push(part)
          logger.error('today_part_load_failed', { part, detail: apiError.detail, status: apiError.status })
        }
      })
    )
    logger.info('today_loaded', { day, failed })
    return failed
  }

  // A resume and the rollover poll can land together, so a second call shares
  // the load in flight rather than racing it.
  let inFlight: Promise<TodayPart[]> | null = null

  /** Load every list on the page. Returns the parts that failed. */
  function load(): Promise<TodayPart[]> {
    inFlight ??= loadEverything().finally(() => {
      inFlight = null
    })
    return inFlight
  }

  /**
   * Reload when the clock has left the day the page shows. The check reads the
   * habit board's day rather than `today`, because undoing a habit reloads the
   * board and moves `today` without reloading the rest of the page.
   */
  async function syncDay(): Promise<TodayPart[]> {
    const clock = todayKey()
    if (habits.selectedDate === clock) return []
    logger.info('today_day_rolled_over', { from: habits.selectedDate, to: clock })
    return load()
  }

  async function addTask(name: string, category: TaskCategory): Promise<Task> {
    return tasks.create({ name, category })
  }

  async function addShoppingItem(name: string): Promise<ShoppingItem> {
    return shopping.addItem({ name })
  }

  async function completeTask(task: Task) {
    const done = await tasks.complete(task.id)
    doneTasks.value = [done, ...doneTasks.value]
  }

  async function reopenTask(task: CompletedTask) {
    await tasks.reopen(task.id)
    doneTasks.value = doneTasks.value.filter((done) => done.id !== task.id)
  }

  async function checkHabit(habit: Habit) {
    await habits.completeHabit(habit, today.value)
  }

  async function uncheckHabit(completion: HabitCompleted) {
    await habits.deleteCompleted(completion.id)
  }

  return {
    today,
    doneTasks,
    status,
    error,
    openTasks,
    openTaskCount,
    habitsDue,
    habitsDone,
    habitsLeft,
    comingUpRows,
    shoppingCount,
    load,
    syncDay,
    addTask,
    addShoppingItem,
    completeTask,
    reopenTask,
    checkHabit,
    uncheckHabit,
  }
})
