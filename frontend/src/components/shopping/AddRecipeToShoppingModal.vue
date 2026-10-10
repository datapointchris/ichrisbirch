<template>
  <AddEditModal
    :visible="visible"
    @close="emit('close')"
  >
    <template #default="{ handleClose, handleSuccess }">
      <form
        class="add-edit-modal__form"
        data-testid="add-edit-modal"
        @submit.prevent="handleSubmit(handleSuccess)"
      >
        <h2>Add to Shopping List</h2>
        <p class="recipe-to-shopping__servings">{{ recipe.name }} · {{ servings }} servings</p>

        <ul class="recipe-to-shopping__ingredients">
          <li
            v-for="ing in recipe.ingredients"
            :key="ing.id"
          >
            <label
              class="recipe-to-shopping__ingredient"
              data-testid="recipe-to-shopping-ingredient"
            >
              <input
                v-model="chosen"
                type="checkbox"
                :value="ing.id"
                data-testid="recipe-to-shopping-checkbox"
              />
              <span class="recipe-to-shopping__item">{{ ing.item }}</span>
              <span class="recipe-to-shopping__amount">{{ ingredientAmount(ing) }}</span>
              <span
                v-if="ing.is_optional"
                class="recipe-to-shopping__optional"
                >optional</span
              >
            </label>
          </li>
        </ul>

        <div class="add-edit-modal__form-buttons">
          <button
            type="submit"
            data-testid="recipe-to-shopping-submit-button"
            class="button"
            :disabled="chosen.length === 0"
          >
            <span class="button__text">Add {{ chosen.length }}</span>
          </button>
          <button
            type="button"
            data-testid="recipe-to-shopping-cancel-button"
            class="button button--danger"
            @click="handleClose()"
          >
            <span class="button__text button__text--danger">Cancel</span>
          </button>
        </div>
      </form>
    </template>
  </AddEditModal>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Recipe, RecipeIngredient, ShoppingItemCreate } from '@/api/client'
import AddEditModal from '@/components/AddEditModal.vue'
import { ingredientAmount } from '@/composables/ingredientAmount'

type Ingredient = Pick<RecipeIngredient, 'item' | 'quantity' | 'scaled_quantity' | 'unit'>

// One item per name with its amounts summed by unit, because the server keeps a repeated note once.
function itemsFor(ingredients: Ingredient[], recipeName: string): ShoppingItemCreate[] {
  const byName = new Map<string, { name: string; totals: Map<string, number | null> }>()
  for (const ing of ingredients) {
    const name = ing.item.trim()
    const key = name.toLowerCase()
    const entry = byName.get(key) ?? { name, totals: new Map<string, number | null>() }
    byName.set(key, entry)
    const unit = ing.unit ?? ''
    const quantity = ing.scaled_quantity ?? ing.quantity
    const total = entry.totals.get(unit) ?? null
    entry.totals.set(unit, quantity === null || quantity === undefined ? total : (total ?? 0) + quantity)
  }
  return [...byName.values()].map(({ name, totals }) => {
    const amount = [...totals]
      .map(([unit, quantity]) => ingredientAmount({ quantity, scaled_quantity: null, unit: unit || null }))
      .filter(Boolean)
      .join(' + ')
    return { name, note: amount ? `${amount} · ${recipeName}` : recipeName }
  })
}

const props = defineProps<{
  visible: boolean
  recipe: Recipe
  servings: number
}>()

const emit = defineEmits<{
  close: []
  add: [items: ShoppingItemCreate[]]
}>()

const chosen = ref<number[]>([])

// Every ingredient starts chosen except an optional one, which is the cook's call each time.
watch(
  () => props.visible,
  (visible) => {
    if (visible) chosen.value = props.recipe.ingredients.filter((ing) => !ing.is_optional).map((ing) => ing.id)
  },
  { immediate: true }
)

function handleSubmit(handleSuccess: () => void) {
  const items = itemsFor(
    props.recipe.ingredients.filter((ing) => chosen.value.includes(ing.id)),
    props.recipe.name
  )
  if (items.length === 0) return
  emit('add', items)
  handleSuccess()
}
</script>

<style scoped lang="scss">
.recipe-to-shopping__ingredients {
  display: flex;
  flex-direction: column;
  max-height: 50vh;
  overflow-y: auto;
  text-align: left;
}

.recipe-to-shopping__ingredient {
  display: flex;
  align-items: center;
  gap: var(--space-2xs);
  min-height: 44px;
}

.recipe-to-shopping__item {
  flex: 1;
}
</style>
