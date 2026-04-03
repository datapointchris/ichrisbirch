import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import AutoFunView from '../AutoFunView.vue'
import { useAutoFunStore } from '@/stores/autofun'
import { useAuthStore } from '@/stores/auth'
import type { AutoFun } from '@/api/types'

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

const activeItems: AutoFun[] = [
  {
    id: 1,
    name: 'Go to the Japanese Tea Garden',
    notes: 'Free on weekday mornings',
    is_completed: false,
    added_date: '2026-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: 'Hike the Dipsea Trail',
    is_completed: false,
    added_date: '2026-01-05T00:00:00Z',
  },
]

const completedItems: AutoFun[] = [
  {
    id: 3,
    name: 'Watch a film at the Castro',
    is_completed: true,
    completed_date: '2026-02-14T00:00:00Z',
    added_date: '2026-01-10T00:00:00Z',
  },
]

const testPreferences = {
  theme_color: 'blue',
  font_family: 'Inter',
  dark_mode: true,
  notifications: false,
  dashboard_layout: [],
  autofun: {
    interval_days: 7,
    max_concurrent: 1,
    is_paused: false,
    task_priority: 7,
  },
}

function createWrapper(autofunState: Record<string, unknown> = {}, authState: Record<string, unknown> = {}) {
  return mount(AutoFunView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            autofun: {
              items: [],
              loading: false,
              error: null,
              ...autofunState,
            },
            auth: {
              user: null,
              preferences: testPreferences,
              loading: false,
              error: null,
              ...authState,
            },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
      stubs: {
        AddEditAutoFunModal: true,
      },
    },
  })
}

describe('AutoFunView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // --- Mount ---

  it('calls fetchAll on mount', () => {
    createWrapper()
    const store = useAutoFunStore()
    expect(store.fetchAll).toHaveBeenCalledOnce()
  })

  // --- Tab navigation ---

  it('shows fun list tab by default', () => {
    const wrapper = createWrapper()
    expect(wrapper.find('[data-testid="autofun-tab-list"]').classes()).toContain('autofun-tabs__tab--active')
    expect(wrapper.find('[data-testid="autofun-add-button"]').exists()).toBe(true)
  })

  it('switches to scheduler tab on click', async () => {
    const wrapper = createWrapper()
    await wrapper.find('[data-testid="autofun-tab-scheduler"]').trigger('click')
    expect(wrapper.find('[data-testid="autofun-tab-scheduler"]').classes()).toContain('autofun-tabs__tab--active')
    expect(wrapper.find('[data-testid="autofun-save-settings-button"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="autofun-add-button"]').exists()).toBe(false)
  })

  // --- Fun list rendering ---

  it('renders loading state', () => {
    const wrapper = createWrapper({ loading: true })
    expect(wrapper.text()).toContain('Loading...')
  })

  it('renders active items only by default', () => {
    const wrapper = createWrapper({ items: [...activeItems, ...completedItems] })
    const items = wrapper.findAll('[data-testid="autofun-item"]')
    expect(items).toHaveLength(2)
    expect(wrapper.text()).toContain('Go to the Japanese Tea Garden')
    expect(wrapper.text()).not.toContain('Watch a film at the Castro')
  })

  it('shows completed items when toggle is checked', async () => {
    const wrapper = createWrapper({ items: [...activeItems, ...completedItems] })
    await wrapper.find('[data-testid="autofun-show-completed"]').setValue(true)
    const items = wrapper.findAll('[data-testid="autofun-item"]')
    expect(items).toHaveLength(3)
    expect(wrapper.text()).toContain('Watch a film at the Castro')
  })

  it('shows empty state when no active items', () => {
    const wrapper = createWrapper({ items: [] })
    expect(wrapper.text()).toContain('No active activities')
  })

  it('shows notes when present', () => {
    const wrapper = createWrapper({ items: activeItems })
    expect(wrapper.text()).toContain('Free on weekday mornings')
  })

  it('does not show edit/delete buttons for completed items', async () => {
    const wrapper = createWrapper({ items: completedItems })
    await wrapper.find('[data-testid="autofun-show-completed"]').setValue(true)
    const item = wrapper.find('[data-testid="autofun-item"]')
    expect(item.find('[data-testid="autofun-edit-button"]').exists()).toBe(false)
    expect(item.find('[data-testid="autofun-delete-button"]').exists()).toBe(false)
  })

  // --- Store action wiring ---

  it('calls remove when delete button clicked', async () => {
    const wrapper = createWrapper({ items: activeItems })
    const store = useAutoFunStore()
    await wrapper.find('[data-testid="autofun-delete-button"]').trigger('click')
    expect(store.remove).toHaveBeenCalledWith(1)
  })

  // --- Modal wiring ---

  it('opens add modal on add button click', async () => {
    const wrapper = createWrapper()
    expect(wrapper.findComponent({ name: 'AddEditAutoFunModal' }).props('visible')).toBe(false)
    await wrapper.find('[data-testid="autofun-add-button"]').trigger('click')
    expect(wrapper.findComponent({ name: 'AddEditAutoFunModal' }).props('visible')).toBe(true)
    expect(wrapper.findComponent({ name: 'AddEditAutoFunModal' }).props('editData')).toBeNull()
  })

  it('opens edit modal with item data', async () => {
    const wrapper = createWrapper({ items: activeItems })
    await wrapper.find('[data-testid="autofun-edit-button"]').trigger('click')
    const modal = wrapper.findComponent({ name: 'AddEditAutoFunModal' })
    expect(modal.props('visible')).toBe(true)
    expect(modal.props('editData')).toEqual(activeItems[0])
  })

  // --- Scheduler tab ---

  it('saves settings by calling updatePreferences', async () => {
    const wrapper = createWrapper()
    await wrapper.find('[data-testid="autofun-tab-scheduler"]').trigger('click')

    await wrapper.find('.autofun-scheduler__form').trigger('submit')

    const auth = useAuthStore()
    expect(auth.updatePreferences).toHaveBeenCalledWith({
      autofun: { interval_days: 7, max_concurrent: 1, is_paused: false, task_priority: 7 },
    })
  })

  it('shows active status when scheduler is not paused', async () => {
    const wrapper = createWrapper()
    await wrapper.find('[data-testid="autofun-tab-scheduler"]').trigger('click')
    expect(wrapper.text()).toContain('Active')
  })
})
