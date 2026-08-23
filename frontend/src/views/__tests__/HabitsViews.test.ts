import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import HabitsView from '../HabitsView.vue'
import HabitsManageView from '../HabitsManageView.vue'
import HabitsCompletedView from '../HabitsCompletedView.vue'
import { useHabitsStore, todayKey } from '@/stores/habits'
import DatePicker from '@/components/DatePicker.vue'
import type { Habit, HabitCategory, HabitCompleted } from '@/api/client'

vi.mock('@/composables/useNotifications', () => ({
  useNotifications: () => ({
    show: vi.fn(),
    close: vi.fn(),
    closeAll: vi.fn(),
    notifications: { value: [] },
  }),
}))

vi.mock('@/composables/formatDate', () => ({
  formatDate: (date: string) => `formatted:${date}`,
}))

vi.mock('vue-chartjs', () => ({
  Bar: { template: '<canvas data-testid="bar-chart"></canvas>', props: ['data', 'options'] },
}))

vi.mock('chart.js', () => ({
  Chart: { register: vi.fn() },
  CategoryScale: {},
  LinearScale: {},
  BarElement: {},
  Title: {},
  Tooltip: {},
}))

const catHealth: HabitCategory = { id: 1, name: 'Health', is_current: true }
const catWork: HabitCategory = { id: 2, name: 'Work', is_current: true }
const catOld: HabitCategory = { id: 3, name: 'Old', is_current: false }

const testHabits: Habit[] = [
  { id: 1, name: 'Exercise', category_id: 1, category: catHealth, is_current: true },
  { id: 2, name: 'Read', category_id: 2, category: catWork, is_current: true },
  { id: 3, name: 'Nap', category_id: 3, category: catOld, is_current: false },
]

const testCompleted: HabitCompleted[] = [
  { id: 10, name: 'Exercise', category_id: 1, category: catHealth, complete_date: '2026-03-29T12:00:00Z' },
]

const testCategories: HabitCategory[] = [catHealth, catWork, catOld]

// --- HabitsView (Daily) ---

function createDailyWrapper(storeState: Record<string, unknown> = {}) {
  return mount(HabitsView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            habits: {
              habits: [],
              categories: [],
              completedHabits: [],
              loading: false,
              error: null,
              selectedFilter: 'this_week',
              ...storeState,
            },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
      stubs: {
        AppSubnav: true,
      },
    },
  })
}

describe('HabitsView (Daily)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls fetchDailyData on mount', () => {
    createDailyWrapper()
    const store = useHabitsStore()
    expect(store.fetchDailyData).toHaveBeenCalledOnce()
  })

  it('renders loading state', () => {
    const wrapper = createDailyWrapper({ loading: true })
    expect(wrapper.text()).toContain('Loading...')
  })

  it('renders "All done" when todo habits are empty and completed exist', () => {
    const wrapper = createDailyWrapper({
      habits: testHabits,
      completedHabits: [
        { id: 10, name: 'Exercise', category_id: 1, category: catHealth, complete_date: '2026-03-29T12:00:00Z' },
        { id: 11, name: 'Read', category_id: 2, category: catWork, complete_date: '2026-03-29T12:00:00Z' },
      ],
    })
    expect(wrapper.text()).toContain('All done for today!')
  })

  it('renders todo habits grouped by category', () => {
    const wrapper = createDailyWrapper({
      habits: testHabits,
      completedHabits: testCompleted,
    })
    // Exercise is completed, so only Read should be in todo
    const todoColumn = wrapper.findAll('.habits__column')[0]!
    expect(todoColumn.text()).toContain('Read')
    expect(todoColumn.text()).toContain('Work')
    expect(todoColumn.text()).not.toContain('Exercise')
  })

  it('renders done habits with done CSS class', () => {
    const wrapper = createDailyWrapper({
      habits: testHabits,
      completedHabits: testCompleted,
    })
    const doneItems = wrapper.findAll('.habits__item--done')
    expect(doneItems.length).toBeGreaterThan(0)
    expect(doneItems[0]!.text()).toContain('Exercise')
  })

  it('calls completeHabit when check button clicked', async () => {
    const wrapper = createDailyWrapper({
      habits: testHabits,
      completedHabits: [],
    })
    const store = useHabitsStore()
    vi.mocked(store.completeHabit).mockResolvedValue({
      id: 99,
      name: 'Exercise',
      category_id: 1,
      category: catHealth,
      complete_date: '2026-03-29T12:00:00Z',
    })

    const checkButton = wrapper.find('.habits__check')
    await checkButton.trigger('click')

    expect(store.completeHabit).toHaveBeenCalledOnce()
  })

  it('steps back a day when the previous arrow is clicked', async () => {
    const wrapper = createDailyWrapper()
    const store = useHabitsStore()

    await wrapper.find('[data-testid="habits-prev-day"]').trigger('click')

    expect(store.stepDay).toHaveBeenCalledWith(-1)
  })

  it('disables the next arrow on today and enables it on an earlier day', async () => {
    const onToday = createDailyWrapper({ selectedDate: todayKey() })
    expect(onToday.find('[data-testid="habits-next-day"]').attributes('disabled')).toBeDefined()

    const earlier = createDailyWrapper({ selectedDate: '2026-03-11' })
    expect(earlier.find('[data-testid="habits-next-day"]').attributes('disabled')).toBeUndefined()
  })

  it('offers a return to today only when off today', () => {
    const onToday = createDailyWrapper({ selectedDate: todayKey() })
    expect(onToday.find('[data-testid="habits-today"]').exists()).toBe(false)

    const earlier = createDailyWrapper({ selectedDate: '2026-03-11' })
    expect(earlier.find('[data-testid="habits-today"]').exists()).toBe(true)
  })

  it('selects the day the picker emits', async () => {
    const wrapper = createDailyWrapper({ selectedDate: todayKey() })
    const store = useHabitsStore()

    await wrapper.findComponent(DatePicker).vm.$emit('update:modelValue', '2026-03-11')

    expect(store.selectDay).toHaveBeenCalledWith('2026-03-11')
  })

  it('ignores a cleared picker rather than selecting an empty day', async () => {
    const wrapper = createDailyWrapper({ selectedDate: '2026-03-11' })
    const store = useHabitsStore()

    await wrapper.findComponent(DatePicker).vm.$emit('update:modelValue', '')

    expect(store.selectDay).not.toHaveBeenCalled()
  })

  it('caps the picker at today so a future day cannot be filled in', () => {
    const wrapper = createDailyWrapper({ selectedDate: '2026-03-11' })
    expect(wrapper.findComponent(DatePicker).props('max')).toBe(todayKey())
  })

  it('hides the picker Clear controls, which this page cannot act on', () => {
    const wrapper = createDailyWrapper({ selectedDate: '2026-03-11' })
    expect(wrapper.findComponent(DatePicker).props('clearable')).toBe(false)
  })

  it('follows the clock when the tab comes back into view', async () => {
    const wrapper = createDailyWrapper()
    const store = useHabitsStore()
    vi.mocked(store.syncToday).mockResolvedValue(undefined)

    Object.defineProperty(document, 'visibilityState', { value: 'visible', configurable: true })
    document.dispatchEvent(new Event('visibilitychange'))
    await wrapper.vm.$nextTick()

    expect(store.syncToday).toHaveBeenCalled()
  })

  it('follows the clock while the tab stays open', async () => {
    vi.useFakeTimers()
    const wrapper = createDailyWrapper()
    const store = useHabitsStore()
    vi.mocked(store.syncToday).mockResolvedValue(undefined)

    vi.advanceTimersByTime(60_000)
    await wrapper.vm.$nextTick()

    expect(store.syncToday).toHaveBeenCalled()
    vi.useRealTimers()
  })

  it('stops polling once the page is gone', async () => {
    vi.useFakeTimers()
    const wrapper = createDailyWrapper()
    const store = useHabitsStore()
    vi.mocked(store.syncToday).mockResolvedValue(undefined)

    wrapper.unmount()
    vi.advanceTimersByTime(180_000)

    expect(store.syncToday).not.toHaveBeenCalled()
    vi.useRealTimers()
  })

  it('names the day rather than "today" in the empty states when off today', () => {
    const wrapper = createDailyWrapper({
      selectedDate: '2026-03-11',
      habits: testHabits,
      completedHabits: [
        { id: 10, habit_id: 1, name: 'Exercise', category_id: 1, category: catHealth, complete_date: '2026-03-11T12:00:00Z' },
        { id: 11, habit_id: 2, name: 'Read', category_id: 2, category: catWork, complete_date: '2026-03-11T12:00:00Z' },
      ],
    })
    expect(wrapper.text()).toContain('All done for that day.')
    expect(wrapper.text()).not.toContain('All done for today!')
  })
})

// --- HabitsManageView ---

function createManageWrapper(storeState: Record<string, unknown> = {}) {
  return mount(HabitsManageView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            habits: {
              habits: [],
              categories: [],
              completedHabits: [],
              loading: false,
              error: null,
              selectedFilter: 'this_week',
              ...storeState,
            },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
      stubs: {
        AppSubnav: true,
        AddEditHabitModal: true,
        AddEditCategoryModal: true,
      },
    },
  })
}

describe('HabitsManageView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls fetchManageData on mount', () => {
    createManageWrapper()
    const store = useHabitsStore()
    expect(store.fetchManageData).toHaveBeenCalledOnce()
  })

  it('renders loading state', () => {
    const wrapper = createManageWrapper({ loading: true })
    expect(wrapper.text()).toContain('Loading...')
  })

  it('renders empty state for habits and categories', () => {
    const wrapper = createManageWrapper()
    expect(wrapper.text()).toContain('No current habits.')
    expect(wrapper.text()).toContain('No current categories.')
  })

  it('renders current habits with edit and hibernate buttons', () => {
    const wrapper = createManageWrapper({
      habits: testHabits,
      categories: testCategories,
    })
    const habitItems = wrapper.findAll('[data-testid="habit-item"]')
    expect(habitItems.length).toBe(2) // only current (Exercise, Read)
    expect(habitItems[0]!.text()).toContain('Exercise')
    expect(habitItems[0]!.find('[data-testid="habit-edit-button"]').exists()).toBe(true)
    expect(habitItems[0]!.find('[data-testid="habit-hibernate-button"]').exists()).toBe(true)
  })

  it('renders hibernating habits with revive and delete buttons', () => {
    const wrapper = createManageWrapper({
      habits: testHabits,
      categories: testCategories,
    })
    const hibernating = wrapper.findAll('[data-testid="habit-item-hibernating"]')
    expect(hibernating.length).toBe(1)
    expect(hibernating[0]!.text()).toContain('Nap')
    expect(hibernating[0]!.find('[data-testid="habit-revive-button"]').exists()).toBe(true)
    expect(hibernating[0]!.find('[data-testid="habit-delete-button"]').exists()).toBe(true)
  })

  it('renders current and hibernating categories', () => {
    const wrapper = createManageWrapper({
      habits: testHabits,
      categories: testCategories,
    })
    const currentCats = wrapper.findAll('[data-testid="category-item"]')
    expect(currentCats.length).toBe(2) // Health, Work (is_current=true)

    const hibernatingCats = wrapper.findAll('[data-testid="category-item-hibernating"]')
    expect(hibernatingCats.length).toBe(1) // Old
    expect(hibernatingCats[0]!.text()).toContain('Old')
  })

  it('calls hibernateHabit when hibernate button clicked', async () => {
    const wrapper = createManageWrapper({
      habits: testHabits,
      categories: testCategories,
    })
    const store = useHabitsStore()

    await wrapper.find('[data-testid="habit-hibernate-button"]').trigger('click')

    expect(store.hibernateHabit).toHaveBeenCalledWith(1)
  })

  it('calls reviveHabit when revive button clicked', async () => {
    const wrapper = createManageWrapper({
      habits: testHabits,
      categories: testCategories,
    })
    const store = useHabitsStore()

    await wrapper.find('[data-testid="habit-revive-button"]').trigger('click')

    expect(store.reviveHabit).toHaveBeenCalledWith(3)
  })

  it('calls deleteHabit when delete button clicked', async () => {
    const wrapper = createManageWrapper({
      habits: testHabits,
      categories: testCategories,
    })
    const store = useHabitsStore()

    await wrapper.find('[data-testid="habit-delete-button"]').trigger('click')

    expect(store.deleteHabit).toHaveBeenCalledWith(3)
  })

  it('opens add habit modal', async () => {
    const wrapper = createManageWrapper({
      habits: testHabits,
      categories: testCategories,
    })

    expect(wrapper.findComponent({ name: 'AddEditHabitModal' }).props('visible')).toBe(false)

    await wrapper.find('[data-testid="habit-add-button"]').trigger('click')

    expect(wrapper.findComponent({ name: 'AddEditHabitModal' }).props('visible')).toBe(true)
    expect(wrapper.findComponent({ name: 'AddEditHabitModal' }).props('editData')).toBeNull()
  })

  it('opens edit habit modal with habit data', async () => {
    const wrapper = createManageWrapper({
      habits: testHabits,
      categories: testCategories,
    })

    await wrapper.find('[data-testid="habit-edit-button"]').trigger('click')

    const modal = wrapper.findComponent({ name: 'AddEditHabitModal' })
    expect(modal.props('visible')).toBe(true)
    expect(modal.props('editData')).toEqual({ id: 1, name: 'Exercise', category_id: 1 })
  })

  it('opens add category modal', async () => {
    const wrapper = createManageWrapper()

    await wrapper.find('[data-testid="category-add-button"]').trigger('click')

    expect(wrapper.findComponent({ name: 'AddEditCategoryModal' }).props('visible')).toBe(true)
    expect(wrapper.findComponent({ name: 'AddEditCategoryModal' }).props('editData')).toBeNull()
  })
})

// --- HabitsCompletedView ---

function createCompletedWrapper(storeState: Record<string, unknown> = {}) {
  return mount(HabitsCompletedView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            habits: {
              habits: [],
              categories: [],
              completedHabits: [],
              loading: false,
              error: null,
              selectedFilter: 'this_week',
              ...storeState,
            },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
      stubs: {
        AppSubnav: true,
        Bar: { template: '<canvas data-testid="bar-chart"></canvas>' },
      },
    },
  })
}

describe('HabitsCompletedView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls fetchCompletedFiltered on mount', () => {
    createCompletedWrapper()
    const store = useHabitsStore()
    expect(store.fetchCompletedFiltered).toHaveBeenCalledOnce()
  })

  it('renders date filter radio buttons', () => {
    const wrapper = createCompletedWrapper()
    expect(wrapper.text()).toContain('This Week')
    expect(wrapper.text()).toContain('Last 30')
    expect(wrapper.text()).toContain('All')
  })

  it('renders completed count when habits exist', () => {
    const wrapper = createCompletedWrapper({
      completedHabits: testCompleted,
    })
    expect(wrapper.text()).toContain('1 completed habits')
  })

  it('renders empty state when no completed habits', () => {
    const wrapper = createCompletedWrapper()
    expect(wrapper.text()).toContain('No completed habits for')
  })
})
