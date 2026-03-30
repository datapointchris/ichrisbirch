import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import EventsView from '../EventsView.vue'
import { useEventsStore } from '@/stores/events'
import type { Event } from '@/api/client'

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

const testEvents: Event[] = [
  { id: 1, name: 'Concert', date: '2026-06-15T18:00:00Z', venue: 'Arena', cost: 50, attending: true, url: 'https://example.com' },
  {
    id: 2,
    name: 'Conference',
    date: '2026-07-01T09:00:00Z',
    venue: 'Convention Center',
    cost: 200,
    attending: false,
    notes: 'Bring laptop',
  },
]

function createWrapper(storeState: Record<string, unknown> = {}) {
  return mount(EventsView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            events: {
              events: [],
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
        AddEditEventModal: true,
      },
    },
  })
}

describe('EventsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // --- Rendering ---

  it('calls fetchAll on mount', () => {
    createWrapper()
    const store = useEventsStore()
    expect(store.fetchAll).toHaveBeenCalledOnce()
  })

  it('renders loading state', () => {
    const wrapper = createWrapper({ loading: true })
    expect(wrapper.text()).toContain('Loading...')
  })

  it('renders empty state when no events', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('No Events')
  })

  it('renders event cards with name, venue, and cost', () => {
    const wrapper = createWrapper({ events: testEvents })
    const items = wrapper.findAll('[data-testid="event-item"]')
    expect(items.length).toBe(2)
    expect(items[0]!.text()).toContain('Concert')
    expect(items[0]!.text()).toContain('Arena')
    expect(items[0]!.text()).toContain('$50.00')
  })

  it('highlights attending events', () => {
    const wrapper = createWrapper({ events: testEvents })
    const items = wrapper.findAll('[data-testid="event-item"]')
    expect(items[0]!.classes()).toContain('grid__item--highlighted')
    expect(items[1]!.classes()).not.toContain('grid__item--highlighted')
  })

  it('shows attending button text based on state', () => {
    const wrapper = createWrapper({ events: testEvents })
    const items = wrapper.findAll('[data-testid="event-item"]')
    expect(items[0]!.find('[data-testid="event-attend-button"]').text()).toContain('Attending')
    expect(items[1]!.find('[data-testid="event-attend-button"]').text()).toContain('Attend Event')
  })

  it('renders event URL link when present', () => {
    const wrapper = createWrapper({ events: testEvents })
    const link = wrapper.find('a[href="https://example.com"]')
    expect(link.exists()).toBe(true)
    expect(link.text()).toBe('Event URL')
  })

  it('renders notes when present', () => {
    const wrapper = createWrapper({ events: testEvents })
    expect(wrapper.text()).toContain('Bring laptop')
  })

  // --- Store action wiring ---

  it('calls toggleAttending when attend button clicked', async () => {
    const wrapper = createWrapper({ events: testEvents })
    const store = useEventsStore()

    await wrapper.find('[data-testid="event-attend-button"]').trigger('click')

    expect(store.toggleAttending).toHaveBeenCalledWith(1)
  })

  it('calls remove when delete button clicked', async () => {
    const wrapper = createWrapper({ events: testEvents })
    const store = useEventsStore()

    await wrapper.find('[data-testid="event-delete-button"]').trigger('click')

    expect(store.remove).toHaveBeenCalledWith(1)
  })

  // --- Modal wiring ---

  it('opens add modal on add button click', async () => {
    const wrapper = createWrapper()

    expect(wrapper.findComponent({ name: 'AddEditEventModal' }).props('visible')).toBe(false)

    await wrapper.find('[data-testid="event-add-button"]').trigger('click')

    expect(wrapper.findComponent({ name: 'AddEditEventModal' }).props('visible')).toBe(true)
    expect(wrapper.findComponent({ name: 'AddEditEventModal' }).props('editData')).toBeNull()
  })

  it('opens edit modal with event data', async () => {
    const wrapper = createWrapper({ events: testEvents })

    await wrapper.find('[data-testid="event-edit-button"]').trigger('click')

    const modal = wrapper.findComponent({ name: 'AddEditEventModal' })
    expect(modal.props('visible')).toBe(true)
    expect(modal.props('editData')).toEqual(testEvents[0])
  })
})
