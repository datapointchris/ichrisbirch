import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import CookingTechniquesView from '../CookingTechniquesView.vue'
import { useCookingTechniquesStore } from '@/stores/cookingTechniques'
import type { CookingTechnique } from '@/api/client'

vi.mock('@/composables/useNotifications', () => ({
  useNotifications: () => ({
    show: vi.fn(),
    close: vi.fn(),
    closeAll: vi.fn(),
    notifications: { value: [] },
  }),
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

function makeTechnique(overrides: Partial<CookingTechnique> = {}): CookingTechnique {
  return {
    id: 1,
    name: 'Vinaigrette Ratio',
    slug: 'vinaigrette-ratio',
    category: 'composition_and_ratio',
    summary: '3:1 oil to acid.',
    body: 'Body.',
    why_it_works: null,
    common_pitfalls: null,
    source_url: null,
    source_name: null,
    tags: null,
    rating: 5,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

const testTechniques: CookingTechnique[] = [
  makeTechnique({ id: 1, name: 'Vinaigrette Ratio', category: 'composition_and_ratio' }),
  makeTechnique({ id: 2, name: 'Caramelize Tomato Paste', category: 'flavor_development', rating: 4 }),
  makeTechnique({ id: 3, name: 'Bean Soak', category: 'preservation_and_pre_treatment', rating: null }),
]

function createWrapper(storeState: Record<string, unknown> = {}) {
  return mount(CookingTechniquesView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            cookingTechniques: {
              techniques: [],
              categories: [],
              loading: false,
              error: null,
              categoryFilter: 'all',
              ratingMin: null,
              searchQuery: '',
              isSearchActive: false,
              sortField: 'name',
              sortDirection: 'asc',
              ...storeState,
            },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
      stubs: {
        AppSubnav: true,
        ActionButton: true,
        NeuSelect: true,
        AddEditCookingTechniqueModal: true,
      },
    },
  })
}

describe('CookingTechniquesView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the add button', () => {
    const wrapper = createWrapper()
    expect(wrapper.find('[data-testid="cooking-technique-add-button"]').exists()).toBe(true)
  })

  it('renders technique rows from the store', () => {
    const wrapper = createWrapper({ techniques: testTechniques })
    const rows = wrapper.findAll('[data-testid="cooking-technique-item"]')
    expect(rows).toHaveLength(3)
  })

  it('shows an empty-state message when no techniques match filters', () => {
    const wrapper = createWrapper({ techniques: [] })
    expect(wrapper.text()).toContain('No techniques match the selected filters.')
  })

  it('opens the modal when the add button is clicked', async () => {
    const wrapper = createWrapper()
    await wrapper.find('[data-testid="cooking-technique-add-button"]').trigger('click')
    const modal = wrapper.findComponent({ name: 'AddEditCookingTechniqueModal' })
    expect(modal.props('visible')).toBe(true)
  })

  it('calls store.remove when delete is clicked', async () => {
    const wrapper = createWrapper({ techniques: testTechniques })
    const store = useCookingTechniquesStore()
    const actionButtons = wrapper.findAllComponents({ name: 'ActionButton' })
    const deleteButton = actionButtons.find((b) => b.attributes('data-testid') === 'cooking-technique-delete-button')
    expect(deleteButton).toBeDefined()
    await deleteButton!.vm.$emit('click')
    expect(store.remove).toHaveBeenCalled()
  })

  it('calls store.search when search form is submitted', async () => {
    const wrapper = createWrapper()
    const store = useCookingTechniquesStore()
    const searchInput = wrapper.find('[data-testid="cooking-technique-search-input"]')
    await searchInput.setValue('vinaigrette')
    await wrapper.find('.cooking-techniques__search').trigger('submit.prevent')
    expect(store.search).toHaveBeenCalledWith('vinaigrette')
  })

  it('shows sortable headers', () => {
    const wrapper = createWrapper({ techniques: testTechniques })
    const sortables = wrapper.findAll('.cooking-techniques__sortable')
    expect(sortables.length).toBeGreaterThanOrEqual(3)
  })
})
