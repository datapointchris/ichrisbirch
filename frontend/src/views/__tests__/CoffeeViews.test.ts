// Component integration tests for CoffeeShopsView and CoffeeBeansView.
// E2E counterpart: tests/e2e/coffee.spec.ts (smoke only — CRUD roundtrip)
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import CoffeeShopsView from '../CoffeeShopsView.vue'
import CoffeeBeansView from '../CoffeeBeansView.vue'
import { useCoffeeShopsStore } from '@/stores/coffeeShops'
import { useCoffeeBeansStore } from '@/stores/coffeeBeans'
import type { CoffeeShop, CoffeeBean } from '@/api/client'

vi.mock('@/composables/useNotifications', () => ({
  useNotifications: () => ({
    show: vi.fn(),
    close: vi.fn(),
    closeAll: vi.fn(),
    notifications: { value: [] },
  }),
}))

const testShops: CoffeeShop[] = [
  {
    id: 1,
    name: 'Ritual Coffee Roasters',
    city: 'San Francisco',
    state: 'CA',
    country: 'USA',
    rating: 4.5,
    notes: 'Great pour-overs',
    review: 'Best espresso in the Mission.',
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: 'Blue Bottle Coffee',
    city: 'Oakland',
    state: 'CA',
    country: 'USA',
    rating: 4.0,
    created_at: '2024-02-01T00:00:00Z',
  },
]

const testBeans: CoffeeBean[] = [
  {
    id: 1,
    name: 'Ethiopia Yirgacheffe',
    roaster: 'Ritual Coffee Roasters',
    origin: 'Ethiopia',
    process: 'washed',
    roast_level: 'light',
    brew_method: 'pour-over',
    flavor_notes: 'blueberry, jasmine, citrus',
    rating: 4.8,
    price: 18.5,
    purchase_source: 'Ritual direct',
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: 'Hair Bender',
    roaster: 'Stumptown',
    origin: 'Blend',
    process: 'washed',
    roast_level: 'medium-dark',
    brew_method: 'drip',
    flavor_notes: 'dark chocolate, toffee',
    rating: 4.0,
    review: 'My go-to house blend.',
    notes: 'Polarizing but consistent.',
    created_at: '2024-02-01T00:00:00Z',
  },
]

// ── CoffeeShopsView ────────────────────────────────────────────────────────────

function createShopsWrapper(storeState: Record<string, unknown> = {}) {
  return mount(CoffeeShopsView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            coffeeShops: {
              items: [],
              loading: false,
              error: null,
              sortField: 'name',
              sortDirection: 'asc',
              filterCity: 'all',
              ...storeState,
            },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
      stubs: {
        CoffeeSubnav: true,
        AddEditCoffeeShopModal: true,
        NeuSelect: true,
      },
    },
  })
}

describe('CoffeeShopsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls fetchAll on mount', () => {
    createShopsWrapper()
    const store = useCoffeeShopsStore()
    expect(store.fetchAll).toHaveBeenCalledOnce()
  })

  it('renders loading state', () => {
    const wrapper = createShopsWrapper({ loading: true })
    expect(wrapper.text()).toContain('Loading...')
  })

  it('renders empty state when no shops', () => {
    const wrapper = createShopsWrapper()
    expect(wrapper.text()).toContain('No shops yet')
  })

  it('renders shop cards with name and location', () => {
    const wrapper = createShopsWrapper({ items: testShops })
    const cards = wrapper.findAll('[data-testid="shop-card"]')
    expect(cards.length).toBe(2)
    // Alphabetical sort: "Blue Bottle Coffee" (index 0) before "Ritual Coffee Roasters" (index 1)
    expect(cards[0]!.text()).toContain('Blue Bottle Coffee')
    expect(cards[0]!.text()).toContain('Oakland')
    expect(cards[1]!.text()).toContain('Ritual Coffee Roasters')
    expect(cards[1]!.text()).toContain('San Francisco')
  })

  it('renders notes on shop card', () => {
    const wrapper = createShopsWrapper({ items: testShops })
    // Ritual (index 1 after alpha sort) has notes
    const card = wrapper.findAll('[data-testid="shop-card"]')[1]!
    expect(card.text()).toContain('Great pour-overs')
  })

  it('renders review on shop card', () => {
    const wrapper = createShopsWrapper({ items: testShops })
    // Ritual (index 1 after alpha sort) has a review
    const card = wrapper.findAll('[data-testid="shop-card"]')[1]!
    expect(card.text()).toContain('Best espresso in the Mission.')
  })

  it('does not render review section when shop has no review', () => {
    const wrapper = createShopsWrapper({ items: testShops })
    const cards = wrapper.findAll('[data-testid="shop-card"]')
    // Blue Bottle (index 0 after alpha sort) has no review
    expect(cards[0]!.find('.coffee-shops__card-review').exists()).toBe(false)
  })

  it('renders star dots — filled count matches rating', () => {
    const wrapper = createShopsWrapper({ items: testShops })
    // Ritual (index 1, rating 4.5) rounds to 5 filled stars
    const card = wrapper.findAll('[data-testid="shop-card"]')[1]!
    const filledStars = card.findAll('.coffee-star--filled')
    expect(filledStars.length).toBe(5)
    const allStars = card.findAll('.coffee-star')
    expect(allStars.length).toBe(5)
  })

  it('opens add modal on button click', async () => {
    const wrapper = createShopsWrapper()
    expect(wrapper.findComponent({ name: 'AddEditCoffeeShopModal' }).props('visible')).toBe(false)

    await wrapper.find('[data-testid="add-shop-button"]').trigger('click')

    expect(wrapper.findComponent({ name: 'AddEditCoffeeShopModal' }).props('visible')).toBe(true)
    expect(wrapper.findComponent({ name: 'AddEditCoffeeShopModal' }).props('editData')).toBeNull()
  })

  it('opens edit modal with shop data on edit button click', async () => {
    const wrapper = createShopsWrapper({ items: testShops })

    // First edit button = Blue Bottle (index 0 after alpha sort, testShops[1])
    await wrapper.find('[data-testid="shop-edit-button"]').trigger('click')

    const modal = wrapper.findComponent({ name: 'AddEditCoffeeShopModal' })
    expect(modal.props('visible')).toBe(true)
    expect(modal.props('editData')).toEqual(testShops[1])
  })

  it('calls remove when delete button clicked', async () => {
    const wrapper = createShopsWrapper({ items: testShops })
    const store = useCoffeeShopsStore()

    // First delete button = Blue Bottle (index 0 after alpha sort, id=2)
    await wrapper.find('[data-testid="shop-delete-button"]').trigger('click')

    expect(store.remove).toHaveBeenCalledWith(2)
  })

  it('renders Google Maps link when shop has google_maps_url', () => {
    const shopsWithMap = [{ ...testShops[0], google_maps_url: 'https://maps.google.com/?q=test' }]
    const wrapper = createShopsWrapper({ items: shopsWithMap })
    const mapsLink = wrapper.find('[data-testid="shop-maps-link"]')
    expect(mapsLink.exists()).toBe(true)
    expect(mapsLink.attributes('href')).toBe('https://maps.google.com/?q=test')
  })

  it('does not render Google Maps link when shop has no google_maps_url', () => {
    const wrapper = createShopsWrapper({ items: testShops })
    // testShops[0] has no google_maps_url
    expect(wrapper.find('[data-testid="shop-maps-link"]').exists()).toBe(false)
  })
})

// ── CoffeeBeansView ────────────────────────────────────────────────────────────

function createBeansWrapper(beansState: Record<string, unknown> = {}, shopsState: Record<string, unknown> = {}) {
  return mount(CoffeeBeansView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            coffeeBeans: {
              items: [],
              loading: false,
              error: null,
              sortField: 'name',
              sortDirection: 'asc',
              roastLevelFilter: 'all',
              brewMethodFilter: 'all',
              ...beansState,
            },
            coffeeShops: {
              items: [],
              loading: false,
              error: null,
              sortField: 'name',
              sortDirection: 'asc',
              filterCity: 'all',
              ...shopsState,
            },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
      stubs: {
        CoffeeSubnav: true,
        AddEditCoffeeBeanModal: true,
        NeuSelect: true,
      },
    },
  })
}

describe('CoffeeBeansView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls fetchAll on both stores on mount', () => {
    createBeansWrapper()
    expect(useCoffeeBeansStore().fetchAll).toHaveBeenCalledOnce()
    expect(useCoffeeShopsStore().fetchAll).toHaveBeenCalledOnce()
  })

  it('renders loading state', () => {
    const wrapper = createBeansWrapper({ loading: true })
    expect(wrapper.text()).toContain('Loading...')
  })

  it('renders empty state when no beans', () => {
    const wrapper = createBeansWrapper()
    expect(wrapper.text()).toContain('No beans yet')
  })

  it('renders bean cards with name and roaster', () => {
    const wrapper = createBeansWrapper({ items: testBeans })
    const cards = wrapper.findAll('[data-testid="bean-card"]')
    expect(cards.length).toBe(2)
    expect(cards[0]!.text()).toContain('Ethiopia Yirgacheffe')
    expect(cards[0]!.text()).toContain('Ritual Coffee Roasters')
  })

  it('renders flavor notes as individual pills', () => {
    const wrapper = createBeansWrapper({ items: testBeans })
    const card = wrapper.findAll('[data-testid="bean-card"]')[0]!
    const pills = card.findAll('.coffee-beans__flavor-pill')
    expect(pills.length).toBe(3)
    expect(pills[0]!.text()).toBe('blueberry')
    expect(pills[1]!.text()).toBe('jasmine')
    expect(pills[2]!.text()).toBe('citrus')
  })

  it('renders notes on bean card', () => {
    const wrapper = createBeansWrapper({ items: testBeans })
    const card = wrapper.findAll('[data-testid="bean-card"]')[1]!
    expect(card.text()).toContain('Polarizing but consistent.')
  })

  it('renders review on bean card', () => {
    const wrapper = createBeansWrapper({ items: testBeans })
    const card = wrapper.findAll('[data-testid="bean-card"]')[1]!
    expect(card.text()).toContain('My go-to house blend.')
  })

  it('does not render notes section when bean has no notes', () => {
    const wrapper = createBeansWrapper({ items: testBeans })
    const card = wrapper.findAll('[data-testid="bean-card"]')[0]!
    expect(card.find('.coffee-beans__card-notes').exists()).toBe(false)
  })

  it('does not render review section when bean has no review', () => {
    const wrapper = createBeansWrapper({ items: testBeans })
    const card = wrapper.findAll('[data-testid="bean-card"]')[0]!
    expect(card.find('.coffee-beans__card-review').exists()).toBe(false)
  })

  it('renders price formatted with dollar sign', () => {
    const wrapper = createBeansWrapper({ items: testBeans })
    const card = wrapper.findAll('[data-testid="bean-card"]')[0]!
    expect(card.text()).toContain('$18.50')
  })

  it('renders purchase_source as "From:" when no shop FK', () => {
    const wrapper = createBeansWrapper({ items: testBeans })
    const card = wrapper.findAll('[data-testid="bean-card"]')[0]!
    expect(card.text()).toContain('From: Ritual direct')
  })

  it('renders roast level badge', () => {
    const wrapper = createBeansWrapper({ items: testBeans })
    const card = wrapper.findAll('[data-testid="bean-card"]')[0]!
    expect(card.find('.coffee-beans__card-roast-badge').text()).toBe('light')
  })

  it('opens add modal on button click', async () => {
    const wrapper = createBeansWrapper()
    expect(wrapper.findComponent({ name: 'AddEditCoffeeBeanModal' }).props('visible')).toBe(false)

    await wrapper.find('[data-testid="add-bean-button"]').trigger('click')

    expect(wrapper.findComponent({ name: 'AddEditCoffeeBeanModal' }).props('visible')).toBe(true)
    expect(wrapper.findComponent({ name: 'AddEditCoffeeBeanModal' }).props('editData')).toBeNull()
  })

  it('opens edit modal with bean data on edit button click', async () => {
    const wrapper = createBeansWrapper({ items: testBeans })

    await wrapper.find('[data-testid="bean-edit-button"]').trigger('click')

    const modal = wrapper.findComponent({ name: 'AddEditCoffeeBeanModal' })
    expect(modal.props('visible')).toBe(true)
    expect(modal.props('editData')).toEqual(testBeans[0])
  })

  it('calls remove when delete button clicked', async () => {
    const wrapper = createBeansWrapper({ items: testBeans })
    const store = useCoffeeBeansStore()

    await wrapper.find('[data-testid="bean-delete-button"]').trigger('click')

    expect(store.remove).toHaveBeenCalledWith(1)
  })

  it('renders shop name as source when bean has coffee_shop_id', () => {
    const shopWithId: CoffeeShop = {
      id: 10,
      name: 'Counter Culture',
      created_at: '2024-01-01T00:00:00Z',
    }
    const beanWithShop: CoffeeBean = {
      id: 3,
      name: 'Guatemala Antigua',
      roaster: 'Counter Culture',
      coffee_shop_id: 10,
      created_at: '2024-01-01T00:00:00Z',
    }
    const wrapper = createBeansWrapper({ items: [beanWithShop] }, { items: [shopWithId] })
    const card = wrapper.find('[data-testid="bean-card"]')
    expect(card.text()).toContain('From: Counter Culture')
  })
})
