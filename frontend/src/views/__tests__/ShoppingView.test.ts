import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import ShoppingView from '../ShoppingView.vue'
import { useShoppingStore } from '@/stores/shopping'
import type { ShoppingItem, ShoppingPurchase, ShoppingSection } from '@/api/client'

const mockNotify = vi.fn()
vi.mock('@/composables/useNotifications', () => ({
  useNotifications: () => ({ show: mockNotify }),
}))

// Renders each row through the item slot. A test lands a drop by changing `list` and emitting
// the `change` event vuedraggable would.
vi.mock('vuedraggable', () => ({
  default: {
    name: 'draggable',
    props: ['list', 'itemKey', 'handle', 'group'],
    emits: ['change', 'start', 'end'],
    template:
      '<div><template v-for="(element, index) in list" :key="element[itemKey] ?? index"><slot name="item" :element="element" :index="index" /></template></div>',
  },
}))

function section(id: string, rank: number): ShoppingSection {
  return { id, name: id, rank, created_ts: '2026-10-01T00:00:00Z' }
}

function item(name: string, overrides: Partial<ShoppingItem> = {}): ShoppingItem {
  return {
    id: name,
    name,
    note: null,
    section_id: null,
    section_name: null,
    rank: 1,
    is_needed: true,
    needed_ts: '2026-10-09T00:00:00Z',
    created_ts: '2026-10-01T00:00:00Z',
    purchase_count: 0,
    last_purchased_ts: null,
    ...overrides,
  }
}

const costco = section('Costco', 1)
const grocery = section('Grocery', 2)
const eggs = item('eggs', { section_id: 'Costco', section_name: 'Costco', rank: 1, note: 'the big box https://example.com/eggs' })
const yogurt = item('yogurt', { section_id: 'Grocery', section_name: 'Grocery', rank: 2 })
const bananas = item('bananas', { section_id: 'Grocery', section_name: 'Grocery', rank: 3 })
const coffee = item('coffee', { section_id: 'Costco', section_name: 'Costco', is_needed: false, purchase_count: 6 })
const boughtMilk: ShoppingPurchase = {
  id: 'p-milk',
  item_id: 'milk',
  item_name: 'milk',
  note: null,
  section_name: 'Grocery',
  purchased_ts: '2026-10-10T15:00:00Z',
}

function createWrapper(state: Record<string, unknown> = {}) {
  return mount(ShoppingView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            shopping: {
              sections: [costco, grocery],
              catalog: [eggs, yogurt, bananas, coffee],
              recentPurchases: [boughtMilk],
              loading: false,
              error: null,
              ...state,
            },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
      stubs: {
        Teleport: true,
        AddEditShoppingItemModal: true,
      },
    },
  })
}

function sectionEl(wrapper: ReturnType<typeof createWrapper>, key: string) {
  return wrapper.find(`[data-section="${key}"]`)
}

function namesIn(wrapper: ReturnType<typeof createWrapper>, key: string): string[] {
  return sectionEl(wrapper, key)
    .findAll('[data-testid="shopping-item-edit"]')
    .map((row) => row.text())
}

describe('ShoppingView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('shows each section with its needed items in rank order', () => {
    const wrapper = createWrapper()
    expect(namesIn(wrapper, 'Costco')).toEqual(['eggs'])
    expect(namesIn(wrapper, 'Grocery')).toEqual(['yogurt', 'bananas'])
    expect(wrapper.get('[data-testid="shopping-total"]').text()).toBe('3')
  })

  it('hides Unsorted while it is empty', () => {
    const wrapper = createWrapper()
    expect(sectionEl(wrapper, 'unsorted').isVisible()).toBe(false)
  })

  it('shows a link in a note by its host', () => {
    const wrapper = createWrapper()
    const link = sectionEl(wrapper, 'Costco').get('a')
    expect(link.attributes('href')).toBe('https://example.com/eggs')
    expect(link.text()).toBe('example.com')
  })

  it('a row dropped into another section is sent with that section and the row above it', async () => {
    const wrapper = createWrapper()
    const store = useShoppingStore()
    const target = sectionEl(wrapper, 'Grocery').findComponent({ name: 'draggable' })
    ;(target.props('list') as ShoppingItem[]).splice(1, 0, eggs)

    target.vm.$emit('change', { added: { element: eggs, newIndex: 1 } })
    await flushPromises()

    expect(store.moveItem).toHaveBeenCalledWith('eggs', { section: 'Grocery', after: 'yogurt' })
  })

  it('the list a row left sends nothing', async () => {
    const wrapper = createWrapper()
    const store = useShoppingStore()
    sectionEl(wrapper, 'Costco')
      .findComponent({ name: 'draggable' })
      .vm.$emit('change', { removed: { element: eggs, oldIndex: 0 } })
    await flushPromises()
    expect(store.moveItem).not.toHaveBeenCalled()
  })

  it('a section dragged first is placed before the one below it', async () => {
    const wrapper = createWrapper()
    const store = useShoppingStore()
    const sections = wrapper.findAllComponents({ name: 'draggable' }).find((stub) => stub.classes('shopping__sections'))!
    ;(sections.props('list') as ShoppingSection[]).reverse()

    sections.vm.$emit('change', { moved: { element: grocery, oldIndex: 1, newIndex: 0 } })
    await flushPromises()

    expect(store.moveSection).toHaveBeenCalledWith('Grocery', { before: 'Costco' })
  })

  it('checking an item off strikes it through, then records the purchase', async () => {
    vi.useFakeTimers()
    const wrapper = createWrapper()
    const store = useShoppingStore()

    await sectionEl(wrapper, 'Costco').get('[data-testid="shopping-item-check"]').trigger('click')
    expect(sectionEl(wrapper, 'Costco').get('[data-testid="shopping-item"]').classes()).toContain('shopping-item--checking')
    expect(store.checkOff).not.toHaveBeenCalled()

    await vi.advanceTimersByTimeAsync(300)
    expect(store.checkOff).toHaveBeenCalledWith(eggs)
  })

  it('a refused check-off says why', async () => {
    vi.useFakeTimers()
    const wrapper = createWrapper()
    const store = useShoppingStore()
    vi.mocked(store.checkOff).mockRejectedValueOnce(new Error('offline'))

    await sectionEl(wrapper, 'Costco').get('[data-testid="shopping-item-check"]').trigger('click')
    await vi.advanceTimersByTimeAsync(300)

    expect(mockNotify).toHaveBeenCalledWith(expect.stringContaining('eggs'), 'error')
  })

  it('tapping a section name renames it inline', async () => {
    const wrapper = createWrapper()
    const store = useShoppingStore()

    await sectionEl(wrapper, 'Grocery').get('[data-testid="shopping-section-name"]').trigger('click')
    const input = sectionEl(wrapper, 'Grocery').get('[data-testid="shopping-section-name-input"]')
    await input.setValue('  Trader Joe’s ')
    await input.trigger('keydown', { key: 'Enter' })

    expect(store.renameSection).toHaveBeenCalledWith('Grocery', 'Trader Joe’s')
    expect(sectionEl(wrapper, 'Grocery').find('[data-testid="shopping-section-name-input"]').exists()).toBe(false)
  })

  it('Escape leaves the name as it was', async () => {
    const wrapper = createWrapper()
    const store = useShoppingStore()

    await sectionEl(wrapper, 'Grocery').get('[data-testid="shopping-section-name"]').trigger('click')
    const input = sectionEl(wrapper, 'Grocery').get('[data-testid="shopping-section-name-input"]')
    await input.setValue('Groceries')
    await input.trigger('keydown', { key: 'Escape' })

    expect(store.renameSection).not.toHaveBeenCalled()
  })

  it('deleting a section takes a second tap', async () => {
    const wrapper = createWrapper()
    const store = useShoppingStore()
    const button = sectionEl(wrapper, 'Grocery').get('[data-testid="shopping-section-delete"]')

    await button.trigger('click')
    expect(store.deleteSection).not.toHaveBeenCalled()
    await button.trigger('click')
    expect(store.deleteSection).toHaveBeenCalledWith('Grocery')
  })

  it('a collapsed section hides its items and stays collapsed on this device', async () => {
    const wrapper = createWrapper()

    await sectionEl(wrapper, 'Grocery').get('[data-testid="shopping-section-toggle"]').trigger('click')

    expect(sectionEl(wrapper, 'Grocery').get('[data-testid="shopping-section-items"]').isVisible()).toBe(false)
    expect(JSON.parse(localStorage.getItem('shopping-collapsed') ?? '[]')).toEqual(['Grocery'])
    expect(sectionEl(createWrapper(), 'Grocery').get('[data-testid="shopping-section-items"]').isVisible()).toBe(false)
  })

  it('Enter adds the typed name, clears the box and says where it went', async () => {
    const wrapper = createWrapper()
    const store = useShoppingStore()
    vi.mocked(store.addItem).mockResolvedValueOnce(item('tape'))

    const input = wrapper.get('[data-testid="shopping-add-input"]')
    await input.setValue(' tape ')
    await input.trigger('submit')
    await flushPromises()

    expect(store.addItem).toHaveBeenCalledWith({ name: 'tape' })
    expect((input.element as HTMLInputElement).value).toBe('')
    expect(wrapper.get('[data-testid="shopping-last-added"]').text()).toBe('tape → Unsorted')
  })

  it('typing suggests catalog names, and a suggestion adds that item', async () => {
    const wrapper = createWrapper()
    const store = useShoppingStore()
    vi.mocked(store.addItem).mockResolvedValueOnce({ ...coffee, is_needed: true })

    await wrapper.get('[data-testid="shopping-add-input"]').setValue('cof')
    const suggestion = wrapper.get('[data-testid="shopping-suggestion"]')
    expect(suggestion.text()).toContain('Costco')
    await suggestion.trigger('click')

    expect(store.addItem).toHaveBeenCalledWith({ name: 'coffee' })
  })

  it('offers what was bought before and is off the list', () => {
    const wrapper = createWrapper()
    expect(wrapper.findAll('[data-testid="shopping-buy-again-chip"]').map((chip) => chip.text())).toEqual(['coffee'])
  })

  it('undoes a check-off noticed the next day from Recently bought', async () => {
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date('2026-10-11T15:00:00Z'))
    const wrapper = createWrapper()
    const store = useShoppingStore()

    expect(wrapper.get('[data-testid="shopping-bought-day"]').text()).toBe('Yesterday')
    await wrapper.get('[data-testid="shopping-bought-row"]').trigger('click')

    expect(store.undoPurchase).toHaveBeenCalledWith(boughtMilk)
  })
})
