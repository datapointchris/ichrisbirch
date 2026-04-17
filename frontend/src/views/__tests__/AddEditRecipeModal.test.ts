import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import AddEditRecipeModal from '@/components/recipes/AddEditRecipeModal.vue'
import type { Recipe } from '@/api/client'

vi.mock('@/composables/useNotifications', () => ({
  useNotifications: () => ({
    show: vi.fn(),
    close: vi.fn(),
    closeAll: vi.fn(),
    notifications: { value: [] },
  }),
}))

function makeRecipe(overrides: Partial<Recipe> = {}): Recipe {
  return {
    id: 10,
    name: 'Existing Recipe',
    description: null,
    source_url: null,
    source_name: null,
    prep_time_minutes: 5,
    cook_time_minutes: 10,
    total_time_minutes: 15,
    servings: 2,
    difficulty: 'easy',
    cuisine: 'italian',
    meal_type: 'dinner',
    tags: ['test'],
    instructions: 'Do it.',
    notes: null,
    rating: 4,
    times_made: 1,
    last_made_date: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ingredients: [
      {
        id: 1,
        recipe_id: 10,
        position: 0,
        quantity: 2,
        unit: 'cup',
        item: 'flour',
        prep_note: null,
        is_optional: false,
        ingredient_group: null,
      },
    ],
    ...overrides,
  }
}

function createWrapper(props: { visible: boolean; editData?: Recipe | null }) {
  return mount(AddEditRecipeModal, {
    props,
    global: {
      plugins: [createTestingPinia({ stubActions: true, createSpy: vi.fn })],
      stubs: {
        AddEditModal: {
          template: '<div><slot :handle-close="() => {}" :handle-success="() => {}" /></div>',
        },
        NeuSelect: true,
      },
    },
  })
}

describe('AddEditRecipeModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders Add heading when editData is null', () => {
    const wrapper = createWrapper({ visible: true, editData: null })
    expect(wrapper.text()).toContain('Add Recipe')
  })

  it('renders Edit heading when editData is provided', async () => {
    const wrapper = createWrapper({ visible: true, editData: makeRecipe() })
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('Edit Recipe')
  })

  it('starts with one empty ingredient row', () => {
    const wrapper = createWrapper({ visible: true, editData: null })
    const rows = wrapper.findAll('[data-testid="recipe-ingredient-row"]')
    expect(rows.length).toBe(1)
  })

  it('adds ingredient row when Add Ingredient clicked', async () => {
    const wrapper = createWrapper({ visible: true, editData: null })

    await wrapper.find('[data-testid="recipe-add-ingredient-button"]').trigger('click')

    const rows = wrapper.findAll('[data-testid="recipe-ingredient-row"]')
    expect(rows.length).toBe(2)
  })

  it('removes ingredient row when remove button clicked (keeps at least one)', async () => {
    const wrapper = createWrapper({ visible: true, editData: null })

    await wrapper.find('[data-testid="recipe-add-ingredient-button"]').trigger('click')
    await wrapper.find('[data-testid="recipe-add-ingredient-button"]').trigger('click')

    let rows = wrapper.findAll('[data-testid="recipe-ingredient-row"]')
    expect(rows.length).toBe(3)

    await wrapper.find('[data-testid="recipe-ingredient-remove-0"]').trigger('click')

    rows = wrapper.findAll('[data-testid="recipe-ingredient-row"]')
    expect(rows.length).toBe(2)
  })

  it('populates form from editData on visible transition', async () => {
    const wrapper = createWrapper({ visible: false, editData: makeRecipe() })

    await wrapper.setProps({ visible: true })
    await wrapper.vm.$nextTick()

    const nameInput = wrapper.find('[data-testid="recipe-name-input"]').element as HTMLInputElement
    expect(nameInput.value).toBe('Existing Recipe')

    const ingRows = wrapper.findAll('[data-testid="recipe-ingredient-row"]')
    expect(ingRows.length).toBe(1)
    const itemInput = wrapper.find('[data-testid="recipe-ingredient-item-0"]').element as HTMLInputElement
    expect(itemInput.value).toBe('flour')
  })

  it('emits create with structured ingredients when submitted', async () => {
    const wrapper = createWrapper({ visible: true, editData: null })

    await wrapper.find('[data-testid="recipe-name-input"]').setValue('Pancakes')
    await wrapper.find('[data-testid="recipe-instructions-input"]').setValue('Mix and cook')
    await wrapper.find('[data-testid="recipe-ingredient-item-0"]').setValue('flour')
    await wrapper.find('[data-testid="recipe-ingredient-quantity-0"]').setValue('2')

    await wrapper.find('form').trigger('submit')

    const emitted = wrapper.emitted('create')
    expect(emitted).toBeTruthy()
    const payload = emitted![0]![0] as { name: string; ingredients: Array<{ item: string; quantity: number }> }
    expect(payload.name).toBe('Pancakes')
    expect(payload.ingredients).toHaveLength(1)
    expect(payload.ingredients[0]!.item).toBe('flour')
    expect(payload.ingredients[0]!.quantity).toBe(2)
  })

  it('submit button is disabled when name or ingredient is empty', () => {
    const wrapper = createWrapper({ visible: true, editData: null })
    const submit = wrapper.find('[data-testid="recipe-submit-button"]').element as HTMLButtonElement
    expect(submit.disabled).toBe(true)
  })

  it('emits update with id when submitting edit', async () => {
    const wrapper = createWrapper({ visible: false, editData: makeRecipe() })
    await wrapper.setProps({ visible: true })
    await wrapper.vm.$nextTick()

    await wrapper.find('[data-testid="recipe-name-input"]').setValue('Renamed')
    await wrapper.find('form').trigger('submit')

    const emitted = wrapper.emitted('update')
    expect(emitted).toBeTruthy()
    expect(emitted![0]![0]).toBe(10)
  })
})
