import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import StrainsView from '../StrainsView.vue'
import type { Strain, StrainVocabulary } from '@/api/client'

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

const testStrains: Strain[] = [
  {
    id: 1,
    name: 'Blue Dream',
    breeder: 'Humboldt Seed Company',
    lineage: 'Blueberry x Haze',
    strain_type: 'sativa_dominant',
    status: 'tried',
    thc_percent: 18,
    cbd_percent: 0.1,
    rating: 8,
    effects: ['creative', 'relaxed'],
    flavors: ['berry'],
    terpenes: ['myrcene'],
    tags: ['daytime'],
    notes: 'The reliable daytime one.',
    last_tried_date: '2026-03-14',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: 'Runtz',
    status: 'want_to_try',
    effects: [],
    flavors: [],
    terpenes: [],
    tags: [],
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
]

const testVocabulary: StrainVocabulary = {
  types: [
    { name: 'indica', count: 0 },
    { name: 'sativa_dominant', count: 1 },
  ],
  statuses: [
    { name: 'tried', count: 1 },
    { name: 'want_to_try', count: 1 },
  ],
  effects: [
    { name: 'creative', count: 1 },
    { name: 'relaxed', count: 1 },
  ],
  flavors: [{ name: 'berry', count: 1 }],
  terpenes: [{ name: 'myrcene', count: 1 }],
}

function createWrapper(state: Record<string, unknown> = {}) {
  return mount(StrainsView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            strains: {
              items: [],
              loading: false,
              error: null,
              sortField: 'name',
              sortDirection: 'asc',
              statusFilter: 'all',
              typeFilter: 'all',
              effectFilter: 'all',
              vocabulary: testVocabulary,
              ...state,
            },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
      stubs: {
        AddEditStrainModal: true,
        NeuSelect: true,
      },
    },
  })
}

describe('StrainsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // --- Rendering ---

  it('fetches the strains and the vocabulary on mount', () => {
    const wrapper = createWrapper()
    const store = wrapper.vm.$.appContext.config.globalProperties.$pinia._s.get('strains')
    expect(store.fetchAll).toHaveBeenCalledOnce()
    expect(store.fetchVocabulary).toHaveBeenCalledOnce()
  })

  it('shows a loading line while loading', () => {
    const wrapper = createWrapper({ loading: true })
    expect(wrapper.text()).toContain('Loading...')
  })

  it('shows an empty line when nothing matches', () => {
    const wrapper = createWrapper({ items: [] })
    expect(wrapper.text()).toContain('No strains match the selected filter.')
  })

  it('renders one row per strain', () => {
    const wrapper = createWrapper({ items: testStrains })
    expect(wrapper.findAll('[data-testid="strain-item"]')).toHaveLength(2)
  })

  it('gives each row a class from its status, which is what colors it', () => {
    const wrapper = createWrapper({ items: testStrains })
    const rows = wrapper.findAll('[data-testid="strain-item"]')
    expect(rows[0]!.classes()).toContain('strain--tried')
    expect(rows[1]!.classes()).toContain('strain--want_to_try')
  })

  it('renders the status counters', () => {
    const wrapper = createWrapper({ items: testStrains })
    expect(wrapper.find('[data-testid="strain-filter-tried"]').text()).toContain('Tried: 1')
    expect(wrapper.find('[data-testid="strain-filter-want-to-try"]').text()).toContain('Want to Try: 1')
    expect(wrapper.find('[data-testid="strain-filter-all"]').text()).toContain('Total: 2')
  })

  it('renders a percentage with its sign and leaves an absent one blank', () => {
    const wrapper = createWrapper({ items: testStrains })
    const rows = wrapper.findAll('[data-testid="strain-item"]')
    expect(rows[0]!.text()).toContain('18%')
    expect(rows[1]!.text()).not.toContain('%')
  })

  it('humanizes an underscored type rather than printing the key', () => {
    const wrapper = createWrapper({ items: testStrains })
    expect(wrapper.findAll('[data-testid="strain-item"]')[0]!.text()).toContain('Sativa Dominant')
  })

  // --- Detail expand ---

  it('keeps the detail panel closed until the chevron is clicked', async () => {
    const wrapper = createWrapper({ items: testStrains })
    expect(wrapper.find('.strains__detail--open').exists()).toBe(false)

    await wrapper.findAll('[data-testid="strain-item"]')[0]!.findAll('button')[0]!.trigger('click')
    expect(wrapper.find('.strains__detail--open').exists()).toBe(true)
  })

  it('shows the descriptor lists in the detail panel', async () => {
    const wrapper = createWrapper({ items: testStrains })
    await wrapper.findAll('[data-testid="strain-item"]')[0]!.findAll('button')[0]!.trigger('click')
    const detail = wrapper.find('.strains__detail--open')
    expect(detail.text()).toContain('creative')
    expect(detail.text()).toContain('berry')
    expect(detail.text()).toContain('myrcene')
  })

  it('says a descriptor list is empty rather than leaving a blank', async () => {
    const wrapper = createWrapper({ items: testStrains })
    await wrapper.findAll('[data-testid="strain-item"]')[1]!.findAll('button')[0]!.trigger('click')
    expect(wrapper.find('.strains__detail--open').text()).toContain('none recorded')
  })

  // --- Store action wiring ---

  it('sets the status filter when a counter is clicked', async () => {
    const wrapper = createWrapper({ items: testStrains })
    const store = wrapper.vm.$.appContext.config.globalProperties.$pinia._s.get('strains')
    await wrapper.find('[data-testid="strain-filter-tried"]').trigger('click')
    expect(store.setStatusFilter).toHaveBeenCalledWith('tried')
  })

  it('sets the sort when a header is clicked', async () => {
    const wrapper = createWrapper({ items: testStrains })
    const store = wrapper.vm.$.appContext.config.globalProperties.$pinia._s.get('strains')
    await wrapper.findAll('.strains__sortable')[0]!.trigger('click')
    expect(store.setSort).toHaveBeenCalledWith('name')
  })

  it('removes a strain when delete is clicked', async () => {
    const wrapper = createWrapper({ items: testStrains })
    const store = wrapper.vm.$.appContext.config.globalProperties.$pinia._s.get('strains')
    await wrapper.find('[data-testid="strain-delete-button"]').trigger('click')
    expect(store.remove).toHaveBeenCalledWith(1)
  })

  // --- Modal wiring ---

  it('opens the modal with no edit data on add', async () => {
    const wrapper = createWrapper({ items: testStrains })
    await wrapper.find('[data-testid="strain-add-button"]').trigger('click')
    const modal = wrapper.findComponent({ name: 'AddEditStrainModal' })
    expect(modal.props('visible')).toBe(true)
    expect(modal.props('editData')).toBeNull()
  })

  it('opens the modal carrying the strain on edit', async () => {
    const wrapper = createWrapper({ items: testStrains })
    await wrapper.find('[data-testid="strain-edit-button"]').trigger('click')
    const modal = wrapper.findComponent({ name: 'AddEditStrainModal' })
    expect(modal.props('visible')).toBe(true)
    expect(modal.props('editData')).toEqual(testStrains[0])
  })

  // --- Vocabulary drives the filters ---

  it('builds the type filter options from the fetched vocabulary, counts included', () => {
    const wrapper = createWrapper({ items: testStrains })
    const selects = wrapper.findAllComponents({ name: 'NeuSelect' })
    const typeOptions = selects[0]!.props('options') as { value: string; label: string }[]
    expect(typeOptions[0]).toEqual({ value: 'all', label: 'All Types' })
    expect(typeOptions.map((o) => o.label)).toContain('Indica (0)')
  })
})
