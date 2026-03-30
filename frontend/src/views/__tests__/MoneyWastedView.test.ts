import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import MoneyWastedView from '../MoneyWastedView.vue'
import { useMoneyWastedStore } from '@/stores/moneyWasted'
import type { MoneyWasted } from '@/api/client'

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

const testItems: MoneyWasted[] = [
  { id: 1, item: 'Unused gym membership', amount: 120, date_wasted: '2026-01-15', notes: 'Never went' },
  { id: 2, item: 'Broken gadget', amount: 45.99, date_purchased: '2025-12-01', date_wasted: '2026-02-10' },
]

function createWrapper(storeState: Record<string, unknown> = {}) {
  return mount(MoneyWastedView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            moneyWasted: {
              items: [],
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
        AddEditMoneyWastedModal: true,
      },
    },
  })
}

describe('MoneyWastedView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // --- Rendering ---

  it('calls fetchAll on mount', () => {
    createWrapper()
    const store = useMoneyWastedStore()
    expect(store.fetchAll).toHaveBeenCalledOnce()
  })

  it('renders loading state', () => {
    const wrapper = createWrapper({ loading: true })
    expect(wrapper.text()).toContain('Loading...')
  })

  it('renders empty state when no items', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('No money wasted yet. Lucky you!')
  })

  it('renders total wasted amount', () => {
    const wrapper = createWrapper({ items: testItems })
    expect(wrapper.text()).toContain('Total Money Wasted:')
    expect(wrapper.text()).toContain('$165.99')
  })

  it('renders item rows with formatted data', () => {
    const wrapper = createWrapper({ items: testItems })
    const rows = wrapper.findAll('[data-testid="mw-item"]')
    expect(rows.length).toBe(2)
    // sortedItems orders by date_wasted desc: Broken gadget (Feb), then Unused gym (Jan)
    expect(rows[0]!.text()).toContain('Broken gadget')
    expect(rows[0]!.text()).toContain('$45.99')
    expect(rows[1]!.text()).toContain('Unused gym membership')
    expect(rows[1]!.text()).toContain('Never went')
  })

  it('renders purchase date when present', () => {
    const wrapper = createWrapper({ items: testItems })
    const rows = wrapper.findAll('[data-testid="mw-item"]')
    // Broken gadget (first in sorted order) has purchase date
    expect(rows[0]!.text()).toContain('formatted:2025-12-01')
  })

  // --- Store action wiring ---

  it('calls remove when delete button clicked', async () => {
    const wrapper = createWrapper({ items: testItems })
    const store = useMoneyWastedStore()

    // First rendered item is Broken gadget (id: 2) due to sort
    await wrapper.find('[data-testid="mw-delete-button"]').trigger('click')

    expect(store.remove).toHaveBeenCalledWith(2)
  })

  // --- Modal wiring ---

  it('opens add modal on add button click', async () => {
    const wrapper = createWrapper()

    expect(wrapper.findComponent({ name: 'AddEditMoneyWastedModal' }).props('visible')).toBe(false)

    await wrapper.find('[data-testid="mw-add-button"]').trigger('click')

    expect(wrapper.findComponent({ name: 'AddEditMoneyWastedModal' }).props('visible')).toBe(true)
    expect(wrapper.findComponent({ name: 'AddEditMoneyWastedModal' }).props('editData')).toBeNull()
  })

  it('opens edit modal with entry data', async () => {
    const wrapper = createWrapper({ items: testItems })

    await wrapper.find('[data-testid="mw-edit-button"]').trigger('click')

    const modal = wrapper.findComponent({ name: 'AddEditMoneyWastedModal' })
    expect(modal.props('visible')).toBe(true)
    // First rendered item is Broken gadget (id: 2) due to sort
    expect(modal.props('editData')).toEqual(testItems[1])
  })
})
