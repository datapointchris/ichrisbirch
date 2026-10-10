import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AddRecipeToShoppingModal from '@/components/shopping/AddRecipeToShoppingModal.vue'
import type { Recipe, RecipeIngredient } from '@/api/client'

function ingredient(id: number, item: string, overrides: Partial<RecipeIngredient> = {}): RecipeIngredient {
  return {
    id,
    recipe_id: 1,
    position: id,
    quantity: null,
    unit: null,
    item,
    prep_note: null,
    is_optional: false,
    ingredient_group: null,
    ...overrides,
  }
}

// Scaled from 4 servings to 8, so each quantity shown is the scaled one.
const quiche: Recipe = {
  id: 1,
  name: 'Quiche',
  description: null,
  source_url: null,
  source_name: null,
  prep_time_minutes: null,
  cook_time_minutes: null,
  total_time_minutes: null,
  servings: 4,
  difficulty: null,
  cuisine: null,
  meal_type: null,
  tags: null,
  instructions: 'Bake.',
  notes: null,
  rating: null,
  times_made: 0,
  last_made_date: null,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  ingredients: [
    ingredient(1, 'eggs', { quantity: 6, scaled_quantity: 12 }),
    ingredient(2, 'milk', { quantity: 0.25, scaled_quantity: 0.5, unit: 'cup' }),
    ingredient(3, 'salt', { unit: 'to_taste' }),
    ingredient(4, 'chives', { quantity: 1, scaled_quantity: 2, unit: 'tbsp', is_optional: true }),
    ingredient(5, 'pie crust'),
  ],
}

function mountModal(recipe: Recipe = quiche) {
  return mount(AddRecipeToShoppingModal, {
    props: { visible: true, recipe, servings: 8 },
    global: {
      stubs: {
        AddEditModal: {
          template: '<div><slot :handle-close="() => {}" :handle-success="() => {}" /></div>',
          props: ['visible'],
        },
      },
    },
  })
}

describe('AddRecipeToShoppingModal', () => {
  it('chooses every ingredient except the optional ones', () => {
    const wrapper = mountModal()
    const checked = wrapper.findAll('[data-testid="recipe-to-shopping-checkbox"]').map((box) => (box.element as HTMLInputElement).checked)
    expect(checked).toEqual([true, true, true, false, true])
  })

  it('notes each item with its scaled amount and the recipe', async () => {
    const wrapper = mountModal()
    await wrapper.get('form').trigger('submit')

    expect(wrapper.emitted('add')?.[0]?.[0]).toEqual([
      { name: 'eggs', note: '12 · Quiche' },
      { name: 'milk', note: '1/2 cup · Quiche' },
      { name: 'salt', note: 'to taste · Quiche' },
      { name: 'pie crust', note: 'Quiche' },
    ])
  })

  it('asks for both eggs when a pie takes one in the crust and one in the filling', async () => {
    const pie: Recipe = {
      ...quiche,
      name: 'Pie',
      ingredients: [
        ingredient(1, 'egg', { quantity: 1, ingredient_group: 'crust' }),
        ingredient(2, 'butter', { quantity: 2, unit: 'tbsp', ingredient_group: 'crust' }),
        ingredient(3, 'Egg', { quantity: 1, ingredient_group: 'filling' }),
        ingredient(4, 'butter', { quantity: 0.5, unit: 'cup', ingredient_group: 'filling' }),
      ],
    }
    const wrapper = mountModal(pie)
    await wrapper.get('form').trigger('submit')

    expect(wrapper.emitted('add')?.[0]?.[0]).toEqual([
      { name: 'egg', note: '2 · Pie' },
      { name: 'butter', note: '2 tbsp + 1/2 cup · Pie' },
    ])
  })

  it('adds an optional ingredient once it is ticked', async () => {
    const wrapper = mountModal()
    await wrapper.findAll('[data-testid="recipe-to-shopping-checkbox"]')[3]!.setValue(true)
    await wrapper.get('form').trigger('submit')

    const names = (wrapper.emitted('add')?.[0]?.[0] as { name: string }[]).map((row) => row.name)
    expect(names).toContain('chives')
  })

  it('sends nothing with every box cleared', async () => {
    const wrapper = mountModal()
    for (const box of wrapper.findAll('[data-testid="recipe-to-shopping-checkbox"]')) await box.setValue(false)
    await wrapper.get('form').trigger('submit')

    expect(wrapper.emitted('add')).toBeUndefined()
    expect(wrapper.get('[data-testid="recipe-to-shopping-submit-button"]').attributes('disabled')).toBeDefined()
  })
})
