import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { ApiError } from '@/api/errors'
import type { Countdown, Event, Habit, HabitCompleted, ShoppingItem, Task, TaskCategory } from '@/api/client'
import { daysBetween, todayKey, type DayKey } from '@/composables/calendarDay'
import { wallClockIsPast } from '@/composables/useWallClock'
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

/** The countdowns due today or later, soonest first. */
export function countdownsAhead(countdowns: Countdown[], today: DayKey): Countdown[] {
  return countdowns
    .filter((countdown) => countdown.due_date >= today)
    .sort((a, b) => a.due_date.localeCompare(b.due_date))
    .slice(0, COMING_UP_SHOWN)
}

/** How far off a due day is, in the words a glance reads fastest. */
export function daysUntil(dueDate: string, today: DayKey): string {
  const days = daysBetween(today, dueDate)
  if (days === 0) return 'Today'
  if (days === 1) return 'Tomorrow'
  return `${days} days`
}

/** The events still to happen, from a list already in time order. */
export function eventsAhead(sortedEvents: Event[], now: number = Date.now()): Event[] {
  return sortedEvents.filter((event) => !wallClockIsPast(event, now)).slice(0, COMING_UP_SHOWN)
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

  const today = ref<DayKey>(todayKey())
  const doneTasks = ref<CompletedTask[]>([])
  const loading = ref(false)
  const error = ref<ApiError | null>(null)

  const openTasks = computed(() => tasks.sortedTasks.slice(0, OPEN_TASKS_SHOWN))
  const openTaskCount = computed(() => tasks.tasks.length)
  const habitsDue = computed(() => habits.todoHabits)
  const habitsDone = computed(() => habits.dayCompleted)
  const habitsLeft = computed(() => habits.dayDue.length)
  const countdownsComing = computed(() => countdownsAhead(countdowns.countdowns, today.value))
  const eventsComing = computed(() => eventsAhead(events.sortedEvents))
  const shoppingCount = computed(() => shopping.needed.length)

  async function loadTasks() {
    await tasks.fetchTodo()
    // The tasks store keeps one completed list for every page reading it, so
    // this page takes a copy and leaves the shared one empty, as /tasks does.
    await tasks.fetchCompleted(today.value, today.value)
    doneTasks.value = [...tasks.completedTasks]
    tasks.completedTasks = []
  }

  async function loadHabits() {
    // The habits store reports a failed day load on its `error` rather than throwing.
    await habits.fetchDailyData(today.value)
    if (habits.error) throw habits.error
  }

  /** Load every list on the page. Returns the names of the lists that failed. */
  async function load(): Promise<string[]> {
    loading.value = true
    error.value = null
    today.value = todayKey()
    const parts: [string, Promise<unknown>][] = [
      ['tasks', loadTasks()],
      ['habits', loadHabits()],
      ['countdowns', countdowns.fetchAll()],
      ['events', events.fetchAll()],
      ['shopping', shopping.fetchAll()],
    ]
    const failed: string[] = []
    await Promise.all(
      parts.map(async ([name, promise]) => {
        try {
          await promise
        } catch (e) {
          const apiError = asApiError(e)
          error.value ??= apiError
          failed.push(name)
          logger.error('today_part_load_failed', { part: name, detail: apiError.detail, status: apiError.status })
        }
      })
    )
    loading.value = false
    logger.info('today_loaded', { day: today.value, failed })
    return failed
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
    loading,
    error,
    openTasks,
    openTaskCount,
    habitsDue,
    habitsDone,
    habitsLeft,
    countdownsComing,
    eventsComing,
    shoppingCount,
    load,
    addTask,
    addShoppingItem,
    completeTask,
    reopenTask,
    checkHabit,
    uncheckHabit,
  }
})
