import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import CountdownsView from '../CountdownsView.vue'
import { useCountdownsStore } from '@/stores/countdowns'
import type { Countdown } from '@/api/client'

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

vi.mock('@/composables/useDaysLeft', () => ({
  computeDaysLeft: (date: string) => {
    if (date === '2026-04-05') return { text: '7 days left', urgency: 'two-weeks' }
    if (date === '2025-01-01') return { text: '454 days ago', urgency: 'past' }
    return { text: '820 days left', urgency: 'normal' }
  },
}))

const testCountdowns: Countdown[] = [
  { id: 1, name: 'Birthday', due_date: '2028-06-15', notes: 'Plan party' },
  { id: 2, name: 'Deadline', due_date: '2026-04-05' },
  { id: 3, name: 'Past Event', due_date: '2025-01-01' },
]

function createWrapper(storeState: Record<string, unknown> = {}) {
  return mount(CountdownsView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            countdowns: {
              countdowns: [],
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
        AddEditCountdownModal: true,
      },
    },
  })
}

describe('CountdownsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // --- Rendering ---

  it('calls fetchAll on mount', () => {
    createWrapper()
    const store = useCountdownsStore()
    expect(store.fetchAll).toHaveBeenCalledOnce()
  })

  it('renders loading state', () => {
    const wrapper = createWrapper({ loading: true })
    expect(wrapper.text()).toContain('Loading...')
  })

  it('renders empty state when no countdowns', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('No Countdowns')
  })

  it('renders countdown items with name and days left', () => {
    const wrapper = createWrapper({ countdowns: testCountdowns })
    const items = wrapper.findAll('[data-testid="countdown-item"]')
    expect(items.length).toBe(3)
    // sortedCountdowns orders by due_date asc: Past Event, Deadline, Birthday
    expect(items[2]!.text()).toContain('Birthday')
    expect(items[2]!.text()).toContain('820 days left')
    expect(items[2]!.text()).toContain('Plan party')
  })

  it('applies urgency CSS class based on due date', () => {
    const wrapper = createWrapper({ countdowns: testCountdowns })
    const daysLeftElements = wrapper.findAll('.daysleft')
    // Sorted: Past Event (past), Deadline (two-weeks), Birthday (normal)
    expect(daysLeftElements[0]!.classes()).toContain('past')
    expect(daysLeftElements[1]!.classes()).toContain('two-weeks-left')
  })

  // --- Store action wiring ---

  it('calls remove when delete button clicked', async () => {
    const wrapper = createWrapper({ countdowns: testCountdowns })
    const store = useCountdownsStore()

    // First rendered item is Past Event (id: 3) due to sort
    await wrapper.find('[data-testid="countdown-delete-button"]').trigger('click')

    expect(store.remove).toHaveBeenCalledWith(3)
  })

  // --- Modal wiring ---

  it('opens add modal on add button click', async () => {
    const wrapper = createWrapper()

    expect(wrapper.findComponent({ name: 'AddEditCountdownModal' }).props('visible')).toBe(false)

    await wrapper.find('[data-testid="countdown-add-button"]').trigger('click')

    expect(wrapper.findComponent({ name: 'AddEditCountdownModal' }).props('visible')).toBe(true)
    expect(wrapper.findComponent({ name: 'AddEditCountdownModal' }).props('editData')).toBeNull()
  })

  it('opens edit modal with countdown data', async () => {
    const wrapper = createWrapper({ countdowns: testCountdowns })

    await wrapper.find('[data-testid="countdown-edit-button"]').trigger('click')

    const modal = wrapper.findComponent({ name: 'AddEditCountdownModal' })
    expect(modal.props('visible')).toBe(true)
    // First rendered item is Past Event (id: 3) due to sort
    expect(modal.props('editData')).toEqual({
      id: 3,
      name: 'Past Event',
      due_date: '2025-01-01',
      notes: undefined,
    })
  })
})
