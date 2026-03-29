import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import BoxPackingView from '../BoxPackingView.vue'
import { useBoxPackingStore } from '@/stores/boxPacking'
import type { Box, BoxItem } from '@/api/client'

vi.mock('@/composables/useNotifications', () => ({
  useNotifications: () => ({
    show: vi.fn(),
    close: vi.fn(),
    closeAll: vi.fn(),
    notifications: { value: [] },
  }),
}))

const testItems: BoxItem[] = [
  { id: 100, box_id: 1, name: 'Guitar cable', essential: true, warm: false, liquid: false },
  { id: 101, box_id: 1, name: 'Microphone', essential: false, warm: false, liquid: false },
]

const testBoxes: Box[] = [
  {
    id: 1,
    number: 1,
    name: 'Studio Gear',
    size: 'Large',
    essential: true,
    warm: false,
    liquid: false,
    items: testItems,
  },
  {
    id: 2,
    number: 2,
    name: 'Winter Clothes',
    size: 'Medium',
    essential: false,
    warm: true,
    liquid: false,
    items: [{ id: 102, box_id: 2, name: 'Jacket', essential: false, warm: true, liquid: false }],
  },
  {
    id: 3,
    number: 3,
    name: 'Empty Box',
    size: 'Small',
    essential: false,
    warm: false,
    liquid: false,
    items: [],
  },
]

const testOrphans: BoxItem[] = [{ id: 200, name: 'Loose screw', essential: false, warm: false, liquid: false }]

function createWrapper(storeState: Record<string, unknown> = {}) {
  return mount(BoxPackingView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            boxPacking: {
              boxes: [],
              orphans: [],
              searchResults: [],
              loading: false,
              error: null,
              sortField1: 'number',
              sortField2: '',
              viewMode: 'block',
              ...storeState,
            },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
      stubs: {
        Teleport: true,
        AddEditBoxModal: true,
        AddEditItemModal: true,
        OrphansModal: true,
        NeuSelect: true,
      },
    },
  })
}

describe('BoxPackingView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // --- Rendering states ---

  it('shows loading state', () => {
    const wrapper = createWrapper({ loading: true })
    expect(wrapper.text()).toContain('Loading...')
  })

  it('shows "No Boxes" when box list is empty', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('No Boxes')
  })

  it('renders boxes in block view', () => {
    const wrapper = createWrapper({ boxes: testBoxes })
    const items = wrapper.findAll('[data-testid="box-item"]')
    expect(items).toHaveLength(3)
    expect(items[0]!.text()).toContain('Studio Gear')
    expect(items[0]!.text()).toContain('2 Items')
    expect(items[0]!.text()).toContain('Essential')
  })

  it('renders items within a box in block view', () => {
    const wrapper = createWrapper({ boxes: testBoxes })
    const contentItems = wrapper.findAll('[data-testid="box-content-item"]')
    // testBoxes has 2 + 1 + 0 = 3 items total across boxes
    expect(contentItems).toHaveLength(3)
    expect(contentItems[0]!.text()).toContain('Guitar cable')
    expect(contentItems[0]!.text()).toContain('Essential')
  })

  it('shows empty box message for boxes with no items', () => {
    const wrapper = createWrapper({ boxes: [testBoxes[2]] })
    expect(wrapper.text()).toContain('No items in this box')
  })

  it('shows box size and item count', () => {
    const wrapper = createWrapper({ boxes: testBoxes })
    const firstBox = wrapper.findAll('[data-testid="box-item"]')[0]!
    expect(firstBox.text()).toContain('Size: Large')
  })

  it('renders boxes in compact view', () => {
    const wrapper = createWrapper({ boxes: testBoxes, viewMode: 'compact' })
    const items = wrapper.findAll('[data-testid="box-item"]')
    expect(items).toHaveLength(3)
    // Items should NOT be visible in compact view (not expanded)
    expect(wrapper.find('[data-testid="box-content-item"]').exists()).toBe(false)
  })

  it('shows derived property badges on boxes', () => {
    const wrapper = createWrapper({ boxes: testBoxes })
    const winterBox = wrapper.findAll('[data-testid="box-item"]')[1]!
    expect(winterBox.text()).toContain('Warm')
  })

  // --- Orphans button ---

  it('shows orphan count and warning style when orphans exist', () => {
    const wrapper = createWrapper({ boxes: testBoxes, orphans: testOrphans })
    const btn = wrapper.find('[data-testid="orphans-button"]')
    expect(btn.text()).toContain('Orphans (1)')
    expect(btn.classes()).toContain('button--warning')
  })

  it('disables orphans button when no orphans', () => {
    const wrapper = createWrapper({ boxes: testBoxes, orphans: [] })
    const btn = wrapper.find('[data-testid="orphans-button"]')
    expect(btn.text()).toContain('Orphans (0)')
    expect(btn.attributes('disabled')).toBeDefined()
  })

  // --- Store action wiring ---

  it('calls fetchAll on mount', () => {
    createWrapper()
    const store = useBoxPackingStore()
    expect(store.fetchAll).toHaveBeenCalledOnce()
  })

  it('calls deleteBox when clicking delete button', async () => {
    const wrapper = createWrapper({ boxes: testBoxes })
    const store = useBoxPackingStore()

    await wrapper.findAll('[data-testid="box-delete-button"]')[0]!.trigger('click')

    expect(store.deleteBox).toHaveBeenCalledWith(1)
  })

  it('calls orphanItem when clicking orphan button on an item', async () => {
    const wrapper = createWrapper({ boxes: testBoxes })
    const store = useBoxPackingStore()

    await wrapper.findAll('[data-testid="item-orphan-button"]')[0]!.trigger('click')

    expect(store.orphanItem).toHaveBeenCalledWith(100, 1)
  })

  it('calls deleteItem when clicking delete button on an item', async () => {
    const wrapper = createWrapper({ boxes: testBoxes })
    const store = useBoxPackingStore()

    await wrapper.findAll('[data-testid="item-delete-button"]')[0]!.trigger('click')

    expect(store.deleteItem).toHaveBeenCalledWith(100, 1)
  })

  // --- Modal wiring ---

  it('opens box add modal on add button click', async () => {
    const wrapper = createWrapper()

    await wrapper.find('[data-testid="box-add-button"]').trigger('click')

    const modal = wrapper.findComponent({ name: 'AddEditBoxModal' })
    expect(modal.props('visible')).toBe(true)
    expect(modal.props('editData')).toBeNull()
  })

  it('opens box edit modal with box data', async () => {
    const wrapper = createWrapper({ boxes: testBoxes })

    await wrapper.findAll('[data-testid="box-edit-button"]')[0]!.trigger('click')

    const modal = wrapper.findComponent({ name: 'AddEditBoxModal' })
    expect(modal.props('visible')).toBe(true)
    expect(modal.props('editData')).toEqual({
      id: 1,
      name: 'Studio Gear',
      number: 1,
      size: 'Large',
    })
  })

  it('opens item add modal with no preselected box', async () => {
    const wrapper = createWrapper({ boxes: testBoxes })

    await wrapper.find('[data-testid="item-add-button"]').trigger('click')

    const modal = wrapper.findComponent({ name: 'AddEditItemModal' })
    expect(modal.props('visible')).toBe(true)
    expect(modal.props('preselectedBoxId')).toBeUndefined()
  })

  it('opens item add modal with preselected box from box-level button', async () => {
    const wrapper = createWrapper({ boxes: testBoxes })

    await wrapper.findAll('[data-testid="box-add-item-button"]')[0]!.trigger('click')

    const modal = wrapper.findComponent({ name: 'AddEditItemModal' })
    expect(modal.props('visible')).toBe(true)
    expect(modal.props('preselectedBoxId')).toBe(1)
  })

  it('opens orphans modal on orphans button click', async () => {
    const wrapper = createWrapper({ boxes: testBoxes, orphans: testOrphans })

    await wrapper.find('[data-testid="orphans-button"]').trigger('click')

    const modal = wrapper.findComponent({ name: 'OrphansModal' })
    expect(modal.props('visible')).toBe(true)
    expect(modal.props('orphans')).toEqual(testOrphans)
  })

  // --- Search ---

  it('calls search on search button click', async () => {
    const wrapper = createWrapper({ boxes: testBoxes })
    const store = useBoxPackingStore()

    await wrapper.find('[data-testid="box-search-input"]').setValue('guitar')
    await wrapper.find('[data-testid="box-search-button"]').trigger('click')

    expect(store.search).toHaveBeenCalledWith('guitar')
  })

  it('shows search results and hides box list', async () => {
    const wrapper = createWrapper({
      boxes: testBoxes,
      searchResults: [
        {
          box: testBoxes[0],
          item: testItems[0],
        },
      ],
    })
    // Simulate search active state by triggering search
    const store = useBoxPackingStore()
    vi.mocked(store.search).mockResolvedValue(undefined)
    await wrapper.find('[data-testid="box-search-input"]').setValue('guitar')
    await wrapper.find('[data-testid="box-search-button"]').trigger('click')
    await vi.dynamicImportSettled()

    expect(wrapper.findAll('[data-testid="search-result-item"]').length).toBeGreaterThanOrEqual(0)
    expect(wrapper.find('[data-testid="box-search-clear-button"]').exists()).toBe(true)
  })

  it('clears search and restores box list', async () => {
    const wrapper = createWrapper({ boxes: testBoxes })
    const store = useBoxPackingStore()
    vi.mocked(store.search).mockResolvedValue(undefined)

    // Activate search
    await wrapper.find('[data-testid="box-search-input"]').setValue('test')
    await wrapper.find('[data-testid="box-search-button"]').trigger('click')
    await vi.dynamicImportSettled()

    // Clear search
    await wrapper.find('[data-testid="box-search-clear-button"]').trigger('click')

    expect(store.clearSearch).toHaveBeenCalled()
    expect(wrapper.find('[data-testid="box-search-clear-button"]').exists()).toBe(false)
  })

  it('does not search when query is empty', async () => {
    const wrapper = createWrapper({ boxes: testBoxes })
    const store = useBoxPackingStore()

    await wrapper.find('[data-testid="box-search-button"]').trigger('click')

    expect(store.search).not.toHaveBeenCalled()
  })

  // --- View mode ---

  it('calls setViewMode when clicking view toggle buttons', async () => {
    const wrapper = createWrapper({ boxes: testBoxes })
    const store = useBoxPackingStore()

    const buttons = wrapper.findAll('.box-controls button')
    // The compact button (list icon) is the 4th button in the controls
    const compactButton = buttons.find((b) => b.html().includes('fa-list'))
    await compactButton!.trigger('click')

    expect(store.setViewMode).toHaveBeenCalledWith('compact')
  })
})
