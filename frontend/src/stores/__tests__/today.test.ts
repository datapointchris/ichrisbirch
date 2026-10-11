import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { COMING_UP_SHOWN, comingUp, daysUntil, useTodayStore } from '../today'
import { useTasksStore } from '../tasks'
import { ApiError } from '@/api/errors'
import type { Countdown, Event, Habit, HabitCategory, HabitCompleted, HabitsDay, Task } from '@/api/client'

vi.mock('@/api/client', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

// The day on the clock, moved by a test to walk past midnight.
const clock = vi.hoisted(() => ({ day: '2026-10-10' }))

vi.mock('@/composables/calendarDay', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/composables/calendarDay')>()),
  todayKey: () => clock.day,
}))

import { api } from '@/api/client'
const mockApi = vi.mocked(api)

function task(id: number, name: string, overrides: Partial<Task> = {}): Task {
  return {
    id,
    name,
    category: 'Chore',
    rank_at: `2026-10-0${id}T00:00:00Z`,
    window_days: 7,
    pinned: false,
    add_date: '2026-10-01T00:00:00Z',
    ...overrides,
  }
}

function countdown(id: number, dueDate: string): Countdown {
  return { id, name: `countdown ${id}`, due_date: dueDate }
}

function event(id: number, date: string): Event {
  return { id, name: `event ${id}`, date, timezone: 'UTC', venue: 'Hall', cost: 0, attending: false }
}

const exercise: HabitCategory = { id: 1, name: 'EXERCISE', is_current: true }
const run: Habit = { id: 7, name: 'Morning run', category_id: 1, category: exercise, is_current: true }

const day: HabitsDay = { date: '2026-10-10', timezone: 'UTC', due: [run], completed: [] } as HabitsDay

// Answers each list the page loads, with a failure for any URL named in `failing`.
function serve(data: Record<string, unknown> = {}, failing: string[] = []) {
  mockApi.get.mockImplementation(async (url: string) => {
    if (failing.includes(url)) throw new ApiError({ message: 'down', detail: 'down', status: 503 })
    const defaults: Record<string, unknown> = {
      '/tasks/todo': [task(1, 'trim nails'), task(2, 'clean gutters')],
      '/tasks/completed': [task(3, 'water plants', { complete_date: '2026-10-10T08:00:00Z' })],
      '/habits/day': day,
    }
    return { data: data[url] ?? defaults[url] ?? [] }
  })
}

describe('comingUp', () => {
  const now = Date.parse('2026-10-10T12:00:00Z')

  it('puts countdowns and events in one list by the day they arrive', () => {
    const rows = comingUp(
      [countdown(1, '2027-03-14'), countdown(2, '2026-10-11')],
      [event(3, '2026-11-04T12:00'), event(4, '2026-10-20T12:00')],
      '2026-10-10',
      now
    )
    expect(rows.map((row) => `${row.kind}-${row.id}`)).toEqual(['countdown-2', 'event-4', 'event-3', 'countdown-1'])
  })

  it('orders events on one day by when they happen, after a countdown due that day', () => {
    const rows = comingUp([countdown(1, '2026-10-12')], [event(2, '2026-10-12T19:00'), event(3, '2026-10-12T09:00')], '2026-10-10', now)
    expect(rows.map((row) => row.id)).toEqual([1, 3, 2])
  })

  it('drops a countdown already due and an event whose time at the venue has passed', () => {
    const rows = comingUp(
      [countdown(1, '2026-10-09'), countdown(2, '2026-10-10')],
      [event(3, '2026-10-10T09:00'), event(4, '2026-10-10T19:00')],
      '2026-10-10',
      now
    )
    expect(rows.map((row) => `${row.kind}-${row.id}`)).toEqual(['countdown-2', 'event-4'])
  })

  it(`shows at most ${COMING_UP_SHOWN} across both`, () => {
    const countdowns = Array.from({ length: 4 }, (_, i) => countdown(i, `2026-11-1${i}`))
    const events = Array.from({ length: 4 }, (_, i) => event(10 + i, `2026-12-1${i}T12:00`))
    expect(comingUp(countdowns, events, '2026-10-10', now)).toHaveLength(COMING_UP_SHOWN)
  })
})

describe('daysUntil', () => {
  it('reads today, tomorrow, and a count of days', () => {
    expect(daysUntil('2026-10-10', '2026-10-10')).toBe('Today')
    expect(daysUntil('2026-10-11', '2026-10-10')).toBe('Tomorrow')
    expect(daysUntil('2026-10-20', '2026-10-10')).toBe('10 days')
  })
})

describe('useTodayStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    clock.day = '2026-10-10'
  })

  function dayLoadsFor(day: string) {
    return mockApi.get.mock.calls.filter(([url, config]) => url === '/habits/day' && config?.params?.date === day)
  }

  it("loads today's completed tasks into its own list and leaves the shared one empty", async () => {
    serve()
    const store = useTodayStore()
    const failed = await store.load()

    expect(failed).toEqual([])
    expect(mockApi.get).toHaveBeenCalledWith('/tasks/completed', { params: { start_date: '2026-10-10', end_date: '2026-10-10' } })
    expect(mockApi.get).toHaveBeenCalledWith('/habits/day', { params: { date: '2026-10-10' } })
    expect(store.doneTasks.map((t) => t.name)).toEqual(['water plants'])
    expect(useTasksStore().completedTasks).toEqual([])
    expect(store.openTasks.map((t) => t.name)).toEqual(['trim nails', 'clean gutters'])
    expect(store.habitsLeft).toBe(1)
  })

  it('names the lists that failed and still shows the rest', async () => {
    serve({}, ['/events', '/habits/day'])
    const store = useTodayStore()
    const failed = await store.load()

    expect(failed.sort()).toEqual(['events', 'habits'])
    expect(store.error?.status).toBe(503)
    expect(store.status).toEqual({
      tasks: 'loaded',
      habits: 'failed',
      countdowns: 'loaded',
      events: 'failed',
      shopping: 'loaded',
    })
    expect(store.openTasks).toHaveLength(2)
  })

  it('reloads every list for the new day when a page left visible passes midnight', async () => {
    serve()
    const store = useTodayStore()
    await store.load()
    vi.clearAllMocks()

    expect(await store.syncDay()).toEqual([])
    expect(mockApi.get).not.toHaveBeenCalled()

    clock.day = '2026-10-11'
    await store.syncDay()
    expect(store.today).toBe('2026-10-11')
    expect(dayLoadsFor('2026-10-11')).toHaveLength(1)
    expect(mockApi.get).toHaveBeenCalledWith('/tasks/completed', { params: { start_date: '2026-10-11', end_date: '2026-10-11' } })
  })

  it('still moves to the new day when a habit was undone just after midnight', async () => {
    const completion = { id: 40, habit_id: 7, name: 'Morning run', complete_date: '2026-10-10' } as HabitCompleted
    serve({ '/habits/day': { ...day, completed: [completion], due: [] } })
    const store = useTodayStore()
    await store.load()

    // The undo reloads the board it is on, which is still yesterday's.
    clock.day = '2026-10-11'
    await store.uncheckHabit(completion)
    expect(dayLoadsFor('2026-10-11')).toHaveLength(0)

    await store.syncDay()
    expect(dayLoadsFor('2026-10-11')).toHaveLength(1)
  })

  it('moves a completed task to the top of done today, and reopening it moves it back', async () => {
    serve()
    const store = useTodayStore()
    await store.load()
    const nails = store.openTasks[0]!
    mockApi.patch.mockResolvedValueOnce({ data: { ...nails, complete_date: '2026-10-10T09:00:00Z' } })

    await store.completeTask(nails)
    expect(mockApi.patch).toHaveBeenCalledWith('/tasks/1/complete')
    expect(store.doneTasks.map((t) => t.name)).toEqual(['trim nails', 'water plants'])
    expect(store.openTasks.map((t) => t.name)).toEqual(['clean gutters'])

    mockApi.patch.mockResolvedValueOnce({ data: { ...nails, complete_date: null } })
    await store.reopenTask(store.doneTasks[0]!)
    expect(mockApi.patch).toHaveBeenLastCalledWith('/tasks/1/reopen')
    expect(store.doneTasks.map((t) => t.name)).toEqual(['water plants'])
    expect(store.openTasks.map((t) => t.name)).toEqual(['trim nails', 'clean gutters'])
  })
})
