import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import TodayView from '../TodayView.vue'
import { type PartStatus, type TodayPart, useTodayStore } from '@/stores/today'
import { ApiError } from '@/api/errors'
import type { Countdown, Event as CalendarEvent, Habit, HabitCategory, HabitCompleted, ShoppingItem, Task } from '@/api/client'

const mockNotify = vi.fn()
vi.mock('@/composables/useNotifications', () => ({
  useNotifications: () => ({ show: mockNotify }),
}))

vi.mock('@/composables/calendarDay', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/composables/calendarDay')>()),
  todayKey: () => '2026-10-10',
}))

function task(id: number, name: string, overrides: Partial<Task> = {}): Task {
  return {
    id,
    name,
    category: 'Home',
    rank_at: `2026-10-0${id}T00:00:00Z`,
    window_days: 7,
    pinned: false,
    add_date: '2026-10-01T00:00:00Z',
    ...overrides,
  }
}

const exercise: HabitCategory = { id: 1, name: 'EXERCISE', is_current: true }
const run: Habit = { id: 7, name: 'Morning run', category_id: 1, category: exercise, is_current: true }
const stretched: HabitCompleted = {
  id: 40,
  habit_id: 8,
  name: 'Stretching',
  category_id: 1,
  category: exercise,
  complete_date: '2026-10-10',
}
const gutters = task(1, 'clean gutters')
const watered = { ...task(3, 'water plants'), complete_date: '2026-10-10T08:00:00Z' }
const renewal: Countdown = { id: 5, name: 'Insurance renewal', due_date: '2026-10-11' }
// Noon UTC falls on the same day in every zone a test machine runs in.
const wedding: CalendarEvent = {
  id: 9,
  name: 'Friends wedding',
  date: '2026-11-04T12:00',
  timezone: 'UTC',
  venue: 'Barn',
  cost: 0,
  attending: true,
}
const eggs = { id: 'eggs', name: 'eggs', section_name: 'Costco' } as ShoppingItem

const allLoaded: Record<TodayPart, PartStatus> = {
  tasks: 'loaded',
  habits: 'loaded',
  countdowns: 'loaded',
  events: 'loaded',
  shopping: 'loaded',
}

function createWrapper(status: Partial<Record<TodayPart, PartStatus>> = {}) {
  const pinia = createTestingPinia({
    initialState: {
      tasks: { tasks: [gutters], completedTasks: [], loading: false, error: null },
      habits: {
        dayDue: [run],
        dayCompleted: [stretched],
        selectedDate: '2026-10-10',
        today: '2026-10-10',
        loading: false,
        error: null,
      },
      countdowns: { countdowns: [renewal], loading: false, error: null },
      events: { events: [wedding], loading: false, error: null },
      shopping: { catalog: [{ ...eggs, is_needed: true }], sections: [], recentPurchases: [], loading: false, error: null },
      today: { doneTasks: [watered], status: { ...allLoaded, ...status }, error: null },
    },
    stubActions: true,
    createSpy: vi.fn,
  })
  const store = useTodayStore(pinia)
  vi.mocked(store.load).mockResolvedValue([])
  vi.mocked(store.syncDay).mockResolvedValue([])
  const wrapper = mount(TodayView, {
    global: {
      plugins: [pinia],
      stubs: { RouterLink: { props: ['to'], template: '<a :href="to"><slot /></a>' } },
    },
  })
  return { wrapper, store }
}

describe('TodayView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    vi.useFakeTimers({ now: Date.parse('2026-10-10T12:00:00Z') })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('loads every list when it opens and shows what is open, due and coming', async () => {
    const { wrapper, store } = createWrapper()
    await flushPromises()

    expect(store.load).toHaveBeenCalledOnce()
    expect(wrapper.find('[data-testid="today-task"]').text()).toContain('clean gutters')
    expect(wrapper.find('[data-testid="today-tasks"]').text()).toContain('1 open')
    expect(wrapper.find('[data-testid="today-habit"]').text()).toContain('Morning run')
    expect(wrapper.find('[data-testid="today-shopping"]').text()).toContain('1 on the list')
    expect(wrapper.find('[data-testid="today-countdown"]').text()).toContain('Tomorrow')
    expect(wrapper.find('[data-testid="today-event"]').text()).toContain('25 days')
  })

  it('says a list is loading until it arrives and could not load once it fails, never that it is empty', async () => {
    const { wrapper } = createWrapper({ tasks: 'loading', habits: 'failed', shopping: 'loading', countdowns: 'failed' })
    await flushPromises()

    const tasks = wrapper.find('[data-testid="today-tasks"]').text()
    expect(tasks).toContain('Loading…')
    expect(tasks).not.toContain('open')
    const habits = wrapper.find('[data-testid="today-habits"]').text()
    expect(habits).toContain('Could not load habits')
    expect(habits).not.toContain('No habits due')
    expect(habits).not.toContain('Morning run')
    expect(wrapper.find('[data-testid="today-shopping-count"]').text()).toBe('Loading…')
    const comingUp = wrapper.find('[data-testid="today-coming-up"]')
    expect(comingUp.find('[data-testid="today-event"]').exists()).toBe(true)
    expect(comingUp.find('[data-testid="today-countdown"]').exists()).toBe(false)
    expect(comingUp.text()).toContain('Could not load countdowns')
    expect(comingUp.text()).not.toContain('Nothing coming up')
  })

  it('says which lists did not load', async () => {
    const pinia = createTestingPinia({ stubActions: true, createSpy: vi.fn })
    vi.mocked(useTodayStore(pinia).load).mockResolvedValue(['habits', 'events'])
    mount(TodayView, { global: { plugins: [pinia], stubs: { RouterLink: true } } })
    await flushPromises()

    expect(mockNotify).toHaveBeenCalledWith('Could not load habits, events', 'error')
  })

  it('strikes a task through on the tap and completes it once the strike lands', async () => {
    const { wrapper, store } = createWrapper()
    await flushPromises()

    await wrapper.find('[data-testid="today-task-complete"]').trigger('click')
    expect(wrapper.find('[data-testid="today-task"]').classes()).toContain('today-row--checking')
    expect(store.completeTask).not.toHaveBeenCalled()

    await vi.advanceTimersByTimeAsync(300)
    expect(store.completeTask).toHaveBeenCalledWith(gutters)
  })

  it('reopens a task tapped under done today', async () => {
    const { wrapper, store } = createWrapper()
    await flushPromises()

    await wrapper.find('[data-testid="today-task-done"]').trigger('click')
    expect(store.reopenTask).toHaveBeenCalledWith(watered)
  })

  it('checks a habit off, and undoes one tapped under done today', async () => {
    const { wrapper, store } = createWrapper()
    await flushPromises()

    await wrapper.find('[data-testid="today-habit-check"]').trigger('click')
    await vi.advanceTimersByTimeAsync(300)
    expect(store.checkHabit).toHaveBeenCalledWith(run)

    await wrapper.find('[data-testid="today-habit-done"]').trigger('click')
    expect(store.uncheckHabit).toHaveBeenCalledWith(stretched)
  })

  it('asks for a category before adding a task, then remembers the one chosen', async () => {
    const { wrapper, store } = createWrapper()
    vi.mocked(store.addTask).mockResolvedValue(task(4, 'fix the gate', { category: 'Home' }))
    await flushPromises()

    await wrapper.find('[data-testid="today-add-input"]').setValue('fix the gate')
    await wrapper.find('form').trigger('submit')
    expect(store.addTask).not.toHaveBeenCalled()
    expect(wrapper.find('[data-testid="today-add-note"]').text()).toBe('Pick a category for the task')

    const home = wrapper.findAll('[data-testid="today-category"]').find((chip) => chip.text() === 'Home')!
    await home.trigger('click')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(store.addTask).toHaveBeenCalledWith('fix the gate', 'Home')
    expect(wrapper.find('[data-testid="today-add-note"]').text()).toBe('fix the gate → Home')
    expect(localStorage.getItem('today-task-category')).toBe('Home')
  })

  it('adds to the shopping list in shopping mode and says which section it landed in', async () => {
    const { wrapper, store } = createWrapper()
    vi.mocked(store.addShoppingItem).mockResolvedValue(eggs)
    await flushPromises()

    await wrapper.find('[data-testid="today-mode-shopping"]').trigger('click')
    expect(wrapper.find('[data-testid="today-categories"]').exists()).toBe(false)
    await wrapper.find('[data-testid="today-add-input"]').setValue('eggs')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(store.addShoppingItem).toHaveBeenCalledWith('eggs')
    expect(wrapper.find('[data-testid="today-add-note"]').text()).toBe('eggs → Costco')
    expect(localStorage.getItem('today-add-mode')).toBe('shopping')
  })

  it('keeps the typed name when an add fails', async () => {
    localStorage.setItem('today-task-category', 'Home')
    const { wrapper, store } = createWrapper()
    vi.mocked(store.addTask).mockRejectedValue(new ApiError({ message: 'down', detail: 'down', status: 503 }))
    await flushPromises()

    await wrapper.find('[data-testid="today-add-input"]').setValue('fix the gate')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect((wrapper.find('[data-testid="today-add-input"]').element as HTMLInputElement).value).toBe('fix the gate')
    expect(mockNotify).toHaveBeenCalledWith(expect.stringContaining('Could not add fix the gate'), 'error')
  })

  it('reloads every list each time the installed app resumes, the same day included', async () => {
    const { store } = createWrapper()
    await flushPromises()
    expect(store.load).toHaveBeenCalledOnce()

    document.dispatchEvent(new Event('visibilitychange'))
    await flushPromises()
    document.dispatchEvent(new Event('visibilitychange'))
    await flushPromises()
    expect(store.load).toHaveBeenCalledTimes(3)
  })

  it('checks the clock every minute while a tab stays visible past midnight', async () => {
    const { wrapper, store } = createWrapper()
    await flushPromises()
    expect(store.syncDay).not.toHaveBeenCalled()

    await vi.advanceTimersByTimeAsync(60_000)
    expect(store.syncDay).toHaveBeenCalledOnce()

    wrapper.unmount()
    await vi.advanceTimersByTimeAsync(60_000)
    expect(store.syncDay).toHaveBeenCalledOnce()
  })
})
