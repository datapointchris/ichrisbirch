import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import DurationsView from '../DurationsView.vue'
import { useDurationsStore } from '@/stores/durations'
import type { Duration } from '@/api/client'

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

vi.mock('@/composables/useElapsedTime', () => ({
  computeElapsedTime: () => ({ text: '2 years, 3 months', totalDays: 820 }),
  computeTimeBetween: () => ({ text: '1 year, 6 months' }),
}))

const testDurations: Duration[] = [
  {
    id: 1,
    name: 'Living in Portland',
    start_date: '2020-01-01',
    end_date: '2023-06-15',
    notes: 'Great city',
    color: '#ff6600',
    duration_notes: [
      { id: 10, duration_id: 1, date: '2021-03-15', content: 'Got a dog' },
      { id: 11, duration_id: 1, date: '2022-01-01', content: 'New job' },
    ],
  },
  {
    id: 2,
    name: 'Learning Rust',
    start_date: '2024-01-01',
    duration_notes: [],
  },
]

function createWrapper(storeState: Record<string, unknown> = {}) {
  return mount(DurationsView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            durations: {
              durations: [],
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
        AddEditDurationModal: true,
        NeuSelect: true,
        DatePicker: true,
        Transition: false,
      },
    },
  })
}

describe('DurationsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // --- Rendering ---

  it('calls fetchAll on mount', () => {
    createWrapper()
    const store = useDurationsStore()
    expect(store.fetchAll).toHaveBeenCalledOnce()
  })

  it('renders loading state', () => {
    const wrapper = createWrapper({ loading: true })
    expect(wrapper.text()).toContain('Loading...')
  })

  it('renders empty state when no durations', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('No Durations')
  })

  it('renders duration cards with name and elapsed time', () => {
    const wrapper = createWrapper({ durations: testDurations })
    const cards = wrapper.findAll('[data-testid="duration-item"]')
    expect(cards.length).toBe(2)
    expect(cards[0]!.text()).toContain('Living in Portland')
    expect(cards[0]!.text()).toContain('2 years, 3 months')
    expect(cards[1]!.text()).toContain('Learning Rust')
  })

  it('shows completed title style for ended durations', () => {
    const wrapper = createWrapper({ durations: testDurations })
    const completedTitle = wrapper.find('.duration-card__title--completed')
    expect(completedTitle.exists()).toBe(true)
    expect(completedTitle.text()).toBe('Living in Portland')
  })

  it('applies custom color to card border', () => {
    const wrapper = createWrapper({ durations: testDurations })
    const card = wrapper.find('[data-testid="duration-item"]')
    expect(card.attributes('style')).toContain('border-left-color: rgb(255, 102, 0)')
  })

  it('shows notes toggle with count', () => {
    const wrapper = createWrapper({ durations: testDurations })
    const toggle = wrapper.find('.duration-card__notes-toggle--has-notes')
    expect(toggle.text()).toContain('Notes (2)')
  })

  it('shows "No notes" for durations without notes', () => {
    const wrapper = createWrapper({ durations: testDurations })
    const empty = wrapper.find('.duration-card__notes-toggle--empty')
    expect(empty.text()).toContain('No notes')
  })

  it('shows ongoing text for durations without end date', () => {
    const wrapper = createWrapper({ durations: testDurations })
    const cards = wrapper.findAll('[data-testid="duration-item"]')
    expect(cards[1]!.text()).toContain('ongoing')
  })

  // --- Notes expand ---

  it('expands notes on toggle click', async () => {
    const wrapper = createWrapper({ durations: testDurations })

    expect(wrapper.find('.duration-notes').exists()).toBe(false)

    await wrapper.find('.duration-card__notes-toggle--has-notes').trigger('click')

    expect(wrapper.find('.duration-notes').exists()).toBe(true)
    expect(wrapper.text()).toContain('Got a dog')
    expect(wrapper.text()).toContain('New job')
  })

  // --- Store action wiring ---

  it('calls remove when delete button clicked', async () => {
    const wrapper = createWrapper({ durations: testDurations })
    const store = useDurationsStore()

    await wrapper.find('[data-testid="duration-delete-button"]').trigger('click')

    expect(store.remove).toHaveBeenCalledWith(1)
  })

  it('shows reopen button only for completed durations', () => {
    const wrapper = createWrapper({ durations: testDurations })
    const reopenButtons = wrapper.findAll('[data-testid="duration-reopen-button"]')
    expect(reopenButtons.length).toBe(1) // only the completed one
  })

  // --- Modal wiring ---

  it('opens add modal on add button click', async () => {
    const wrapper = createWrapper()

    expect(wrapper.findComponent({ name: 'AddEditDurationModal' }).props('visible')).toBe(false)

    await wrapper.find('[data-testid="duration-add-button"]').trigger('click')

    expect(wrapper.findComponent({ name: 'AddEditDurationModal' }).props('visible')).toBe(true)
    expect(wrapper.findComponent({ name: 'AddEditDurationModal' }).props('editData')).toBeNull()
  })

  it('opens edit modal with duration data', async () => {
    const wrapper = createWrapper({ durations: testDurations })

    await wrapper.find('[data-testid="duration-edit-button"]').trigger('click')

    const modal = wrapper.findComponent({ name: 'AddEditDurationModal' })
    expect(modal.props('visible')).toBe(true)
    expect(modal.props('editData')).toEqual({
      id: 1,
      name: 'Living in Portland',
      start_date: '2020-01-01',
      end_date: '2023-06-15',
      notes: 'Great city',
      color: '#ff6600',
    })
  })

  // --- Compare mode ---

  it('toggles compare mode on button click', async () => {
    const wrapper = createWrapper({ durations: testDurations })

    expect(wrapper.find('.duration-card__compare').exists()).toBe(false)
    expect(wrapper.text()).toContain('Compare Dates')

    await wrapper.find('.duration-controls .button').trigger('click')

    expect(wrapper.find('.duration-card__compare').exists()).toBe(true)
    expect(wrapper.text()).toContain('Exit Compare')
  })
})
