import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import RecipesImportFromUrlView from '../RecipesImportFromUrlView.vue'
import type { UrlImportCandidate } from '@/api/client'

vi.mock('@/composables/useNotifications', () => ({
  useNotifications: () => ({
    show: vi.fn(),
    close: vi.fn(),
    closeAll: vi.fn(),
    notifications: { value: [] },
  }),
}))

const recipeCandidate = {
  name: 'Classic Chimichurri',
  description: 'Argentinian herb sauce',
  source_url: 'https://www.youtube.com/watch?v=qEb96qFi2Tc',
  source_name: 'Kevin / KWOOWK',
  prep_time_minutes: 10,
  cook_time_minutes: 0,
  total_time_minutes: 10,
  servings: 6,
  difficulty: 'easy',
  cuisine: 'other',
  meal_type: 'sauce',
  tags: ['herb', 'vinaigrette'],
  instructions: 'Chop, mix, rest.',
  notes: null,
  ingredients: [{ position: 0, quantity: 1, unit: 'cup', item: 'parsley', prep_note: null, is_optional: false, ingredient_group: null }],
}

const techniqueCandidate = {
  name: '3:1 Vinaigrette Ratio',
  category: 'composition_and_ratio',
  summary: 'Three parts fat to one part acid.',
  body: 'The 3:1 ratio balances richness against brightness.',
  why_it_works: null,
  common_pitfalls: null,
  source_url: 'https://www.youtube.com/watch?v=qEb96qFi2Tc',
  source_name: 'Kevin / KWOOWK',
  tags: null,
  rating: null,
}

function createWrapper(urlImportCandidate: UrlImportCandidate | null = null, urlImportLoading = false) {
  return mount(RecipesImportFromUrlView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            recipes: {
              recipes: [],
              loading: false,
              error: null,
              aiCandidates: [],
              aiLoading: false,
              urlImportCandidate,
              urlImportLoading,
            },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
      stubs: {
        AppSubnav: true,
        RecipeCandidateCard: true,
      },
    },
  })
}

describe('RecipesImportFromUrlView', () => {
  it('renders URL input and hint radios', () => {
    const wrapper = createWrapper()
    expect(wrapper.find('[data-testid="url-import-url-input"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="url-import-hint-auto"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="url-import-hint-recipe"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="url-import-hint-technique"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="url-import-hint-both"]').exists()).toBe(true)
  })

  it('submit button disabled while loading', () => {
    const wrapper = createWrapper(null, true)
    const submit = wrapper.find<HTMLButtonElement>('[data-testid="url-import-submit"]')
    expect(submit.element.disabled).toBe(true)
  })

  it('submit button disabled when URL is empty', () => {
    const wrapper = createWrapper()
    const submit = wrapper.find<HTMLButtonElement>('[data-testid="url-import-submit"]')
    expect(submit.element.disabled).toBe(true)
  })

  it('shows recipe section only for kind=recipe', () => {
    const wrapper = createWrapper({ kind: 'recipe', recipe: recipeCandidate, technique: null, technique_mention: null })
    expect(wrapper.find('[data-testid="url-import-recipe-section"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="url-import-technique-section"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="url-import-kind-recipe"]').exists()).toBe(true)
  })

  it('shows technique section only for kind=technique', () => {
    const wrapper = createWrapper({ kind: 'technique', recipe: null, technique: techniqueCandidate, technique_mention: null })
    expect(wrapper.find('[data-testid="url-import-recipe-section"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="url-import-technique-section"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="url-import-kind-technique"]').exists()).toBe(true)
  })

  it('shows both sections and mention for kind=both', () => {
    const wrapper = createWrapper({
      kind: 'both',
      recipe: recipeCandidate,
      technique: techniqueCandidate,
      technique_mention: 'Uses the 3:1 vinaigrette ratio technique',
    })
    expect(wrapper.find('[data-testid="url-import-recipe-section"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="url-import-technique-section"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="url-import-mention"]').text()).toContain('Uses the 3:1 vinaigrette ratio technique')
    expect(wrapper.find('[data-testid="url-import-kind-both"]').exists()).toBe(true)
  })

  it('save button label reflects candidate kind', () => {
    const wrapper = createWrapper({
      kind: 'both',
      recipe: recipeCandidate,
      technique: techniqueCandidate,
      technique_mention: null,
    })
    expect(wrapper.find('[data-testid="url-import-save"]').text()).toContain('Recipe + Technique')
  })

  it('does not render result section when there is no candidate', () => {
    const wrapper = createWrapper(null)
    expect(wrapper.find('[data-testid="url-import-result"]').exists()).toBe(false)
  })
})
