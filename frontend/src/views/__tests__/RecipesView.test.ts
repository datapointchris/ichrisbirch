import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import RecipesView from '../RecipesView.vue'
import { useRecipesStore } from '@/stores/recipes'
import type { Recipe } from '@/api/client'

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

function makeRecipe(overrides: Partial<Recipe> = {}): Recipe {
  return {
    id: 1,
    name: 'Spaghetti',
    description: null,
    source_url: null,
    source_name: null,
    prep_time_minutes: 10,
    cook_time_minutes: 20,
    total_time_minutes: 30,
    servings: 4,
    difficulty: 'easy',
    cuisine: 'italian',
    meal_type: 'dinner',
    tags: ['pasta'],
    instructions: 'Boil. Sauce. Eat.',
    notes: null,
    rating: 4,
    times_made: 2,
    last_made_date: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ingredients: [],
    ...overrides,
  }
}

const testRecipes: Recipe[] = [
  makeRecipe({ id: 1, name: 'Spaghetti', cuisine: 'italian' }),
  makeRecipe({ id: 2, name: 'Taco Soup', cuisine: 'mexican', rating: 5, times_made: 0 }),
  makeRecipe({ id: 3, name: 'Pad Thai', cuisine: 'asian', rating: 3 }),
]

function createWrapper(storeState: Record<string, unknown> = {}) {
  return mount(RecipesView, {
    global: {
      plugins: [
        createTestingPinia({
          initialState: {
            recipes: {
              recipes: [],
              loading: false,
              error: null,
              cuisineFilter: 'all',
              mealTypeFilter: 'all',
              difficultyFilter: 'all',
              ratingMin: null,
              searchQuery: '',
              isSearchActive: false,
              sortField: 'name',
              sortDirection: 'asc',
              ingredientSearchResults: [],
              ingredientSearchActive: false,
              aiCandidates: [],
              aiLoading: false,
              ...storeState,
            },
          },
          stubActions: true,
          createSpy: vi.fn,
        }),
      ],
      stubs: {
        AppSubnav: true,
        AddEditRecipeModal: true,
        NeuSelect: true,
      },
    },
  })
}

describe('RecipesView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls fetchAll on mount', () => {
    createWrapper()
    const store = useRecipesStore()
    expect(store.fetchAll).toHaveBeenCalledOnce()
  })

  it('renders loading state', () => {
    const wrapper = createWrapper({ loading: true })
    expect(wrapper.text()).toContain('Loading...')
  })

  it('renders empty state when no recipes match filter', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('No recipes match the selected filters.')
  })

  it('renders recipe rows with name, cuisine, rating, times made', () => {
    const wrapper = createWrapper({ recipes: testRecipes })
    const rows = wrapper.findAll('[data-testid="recipe-item"]')
    expect(rows.length).toBe(3)
    expect(rows[0]!.text()).toContain('Pad Thai') // alphabetical
    expect(rows[0]!.text()).toContain('asian')
  })

  it('shows recipe count in filter bar', () => {
    const wrapper = createWrapper({ recipes: testRecipes })
    expect(wrapper.text()).toContain('3 recipes')
  })

  it('calls remove when delete button clicked', async () => {
    const wrapper = createWrapper({ recipes: testRecipes })
    const store = useRecipesStore()

    await wrapper.find('[data-testid="recipe-delete-button"]').trigger('click')

    expect(store.remove).toHaveBeenCalled()
  })

  it('calls markMade when mark-made button clicked', async () => {
    const wrapper = createWrapper({ recipes: testRecipes })
    const store = useRecipesStore()

    await wrapper.find('[data-testid="recipe-mark-made-button"]').trigger('click')

    expect(store.markMade).toHaveBeenCalled()
  })

  it('opens add modal on add button click', async () => {
    const wrapper = createWrapper()

    expect(wrapper.findComponent({ name: 'AddEditRecipeModal' }).props('visible')).toBe(false)

    await wrapper.find('[data-testid="recipe-add-button"]').trigger('click')

    expect(wrapper.findComponent({ name: 'AddEditRecipeModal' }).props('visible')).toBe(true)
    expect(wrapper.findComponent({ name: 'AddEditRecipeModal' }).props('editData')).toBeNull()
  })

  it('opens edit modal with recipe data on edit button click', async () => {
    const wrapper = createWrapper({ recipes: testRecipes })

    await wrapper.find('[data-testid="recipe-edit-button"]').trigger('click')

    const modal = wrapper.findComponent({ name: 'AddEditRecipeModal' })
    expect(modal.props('visible')).toBe(true)
    // The sorted order puts Pad Thai first alphabetically
    const editData = modal.props('editData') as Recipe
    expect(editData.name).toBe('Pad Thai')
  })

  it('calls search when name search form submitted', async () => {
    const wrapper = createWrapper({ recipes: testRecipes })
    const store = useRecipesStore()

    await wrapper.find('[data-testid="recipe-search-input"]').setValue('pasta')
    await wrapper.find('[data-testid="recipe-search-input"]').trigger('keydown.enter')
    await wrapper.find('[data-testid="recipe-search-button"]').trigger('submit')
    // Also try triggering on the form
    const form = wrapper.find('form.recipes__search')
    await form.trigger('submit')

    expect(store.search).toHaveBeenCalledWith('pasta')
  })

  it('switches to ingredient search mode', async () => {
    const wrapper = createWrapper({ recipes: testRecipes })

    await wrapper.find('[data-testid="recipe-search-mode-ingredients"]').trigger('click')

    expect(wrapper.find('[data-testid="recipe-ingredient-search-input"]').exists()).toBe(true)
  })

  it('calls searchByIngredients when ingredient form submitted', async () => {
    const wrapper = createWrapper({ recipes: testRecipes })
    const store = useRecipesStore()

    await wrapper.find('[data-testid="recipe-search-mode-ingredients"]').trigger('click')
    await wrapper.find('[data-testid="recipe-ingredient-search-input"]').setValue('chicken, lemon')
    await wrapper.find('form.recipes__search').trigger('submit')

    expect(store.searchByIngredients).toHaveBeenCalledWith(['chicken', 'lemon'], 'any')
  })

  it('renders ingredient search results with coverage', () => {
    const results = [
      {
        recipe: testRecipes[0]!,
        coverage: 2,
        total_ingredients: 5,
      },
    ]
    const wrapper = createWrapper({
      recipes: testRecipes,
      ingredientSearchActive: true,
      ingredientSearchResults: results,
    })

    const rows = wrapper.findAll('[data-testid="recipe-match-item"]')
    expect(rows.length).toBe(1)
    expect(rows[0]!.text()).toContain('Spaghetti')
    expect(rows[0]!.text()).toContain('2 of 5 ingredients')
  })

  it('shows empty message for ingredient search with no matches', () => {
    const wrapper = createWrapper({
      recipes: testRecipes,
      ingredientSearchActive: true,
      ingredientSearchResults: [],
    })
    expect(wrapper.text()).toContain('No recipes match those ingredients.')
  })

  it('calls setSort when column header clicked', async () => {
    const wrapper = createWrapper({ recipes: testRecipes })
    const store = useRecipesStore()

    await wrapper.find('.recipes__sortable').trigger('click')

    expect(store.setSort).toHaveBeenCalledWith('name')
  })
})
