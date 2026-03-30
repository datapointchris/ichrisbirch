import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import AutoTasksView from '../AutoTasksView.vue'
import { useAutoTasksStore } from '@/stores/autotasks'
import type { AutoTask } from '@/api/client'

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

const testAutoTasks: AutoTask[] = [
  {
    id: 1,
    name: 'Weekly Cleanup',
    category: 'Chore',
    priority: 5,
    frequency: 'Weekly',
    max_concurrent: 1,
    first_run_date: '2026-01-01T00:00:00Z',
    last_run_date: '2026-03-29T00:00:00Z',
    run_count: 12,
    notes: 'Clean the house',
  },
  {
    id: 2,
    name: 'Monthly Review',
    category: 'Project',
    priority: 3,
    frequency: 'Monthly',
    max_concurrent: 1,
    first_run_date: '2026-01-01T00:00:00Z',
    last_run_date: '2026-03-01T00:00:00Z',
    run_count: 3,
  },
]

function createWrapper(storeState: Record<string, unknown> = {}) {
  return mount(AutoTasksView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            autotasks: {
              autotasks: [],
              loading: false,
              error: null,
              ...storeState,
            },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
      stubs: {
        AddEditAutoTaskModal: true,
      },
    },
  })
}

describe('AutoTasksView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // --- Rendering ---

  it('calls fetchAll on mount', () => {
    createWrapper()
    const store = useAutoTasksStore()
    expect(store.fetchAll).toHaveBeenCalledOnce()
  })

  it('renders loading state', () => {
    const wrapper = createWrapper({ loading: true })
    expect(wrapper.text()).toContain('Loading...')
  })

  it('renders empty state when no autotasks', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('No AutoTasks')
  })

  it('renders autotask cards with details', () => {
    const wrapper = createWrapper({ autotasks: testAutoTasks })
    const items = wrapper.findAll('[data-testid="autotask-item"]')
    expect(items.length).toBe(2)
    expect(items[0]!.text()).toContain('Weekly Cleanup')
    expect(items[0]!.text()).toContain('Chore')
    expect(items[0]!.text()).toContain('Weekly')
    expect(items[0]!.text()).toContain('12')
    expect(items[0]!.text()).toContain('Clean the house')
  })

  it('shows run count and dates', () => {
    const wrapper = createWrapper({ autotasks: testAutoTasks })
    const items = wrapper.findAll('[data-testid="autotask-item"]')
    expect(items[1]!.text()).toContain('3')
    expect(items[1]!.text()).toContain('Monthly')
  })

  // --- Store action wiring ---

  it('calls run when run button clicked', async () => {
    const wrapper = createWrapper({ autotasks: testAutoTasks })
    const store = useAutoTasksStore()

    await wrapper.find('[data-testid="autotask-run-button"]').trigger('click')

    expect(store.run).toHaveBeenCalledWith(1)
  })

  it('calls remove when delete button clicked', async () => {
    const wrapper = createWrapper({ autotasks: testAutoTasks })
    const store = useAutoTasksStore()

    await wrapper.find('[data-testid="autotask-delete-button"]').trigger('click')

    expect(store.remove).toHaveBeenCalledWith(1)
  })

  // --- Modal wiring ---

  it('opens add modal on add button click', async () => {
    const wrapper = createWrapper()

    expect(wrapper.findComponent({ name: 'AddEditAutoTaskModal' }).props('visible')).toBe(false)

    await wrapper.find('[data-testid="autotask-add-button"]').trigger('click')

    expect(wrapper.findComponent({ name: 'AddEditAutoTaskModal' }).props('visible')).toBe(true)
    expect(wrapper.findComponent({ name: 'AddEditAutoTaskModal' }).props('editData')).toBeNull()
  })

  it('opens edit modal with autotask data', async () => {
    const wrapper = createWrapper({ autotasks: testAutoTasks })

    await wrapper.find('[data-testid="autotask-edit-button"]').trigger('click')

    const modal = wrapper.findComponent({ name: 'AddEditAutoTaskModal' })
    expect(modal.props('visible')).toBe(true)
    expect(modal.props('editData')).toEqual(testAutoTasks[0])
  })
})
