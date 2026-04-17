<template>
  <AddEditModal
    :visible="visible"
    :focus-ref="nameInput"
    @close="handleModalClose"
  >
    <template #default="{ handleClose, handleSuccess }">
      <form
        class="add-edit-modal__form recipe-modal__form"
        @submit.prevent="handleSubmit(handleSuccess)"
      >
        <h2>{{ editData ? 'Edit Recipe' : 'Add Recipe' }}</h2>

        <!-- name -->
        <div class="add-edit-modal__form-item">
          <label for="recipe-name">Name</label>
          <input
            id="recipe-name"
            ref="nameInput"
            v-model="form.name"
            data-testid="recipe-name-input"
            type="text"
            class="textbox"
            required
          />
        </div>

        <!-- description -->
        <div class="add-edit-modal__form-item">
          <label for="recipe-description">Description</label>
          <input
            id="recipe-description"
            v-model="form.description"
            data-testid="recipe-description-input"
            type="text"
            class="textbox"
          />
        </div>

        <!-- cuisine, meal_type, difficulty -->
        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="recipe-cuisine">Cuisine</label>
            <NeuSelect
              :model-value="form.cuisine"
              :options="cuisineOptions"
              data-testid="recipe-cuisine-input"
              @update:model-value="form.cuisine = $event"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="recipe-meal-type">Meal Type</label>
            <NeuSelect
              :model-value="form.meal_type"
              :options="mealTypeOptions"
              data-testid="recipe-meal-type-input"
              @update:model-value="form.meal_type = $event"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="recipe-difficulty">Difficulty</label>
            <NeuSelect
              :model-value="form.difficulty"
              :options="difficultyOptions"
              data-testid="recipe-difficulty-input"
              @update:model-value="form.difficulty = $event"
            />
          </div>
        </div>

        <!-- prep, cook, total, servings -->
        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="recipe-prep">Prep (min)</label>
            <input
              id="recipe-prep"
              v-model="form.prep_time_minutes"
              data-testid="recipe-prep-input"
              type="number"
              min="0"
              class="textbox add-edit-modal__number-input"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="recipe-cook">Cook (min)</label>
            <input
              id="recipe-cook"
              v-model="form.cook_time_minutes"
              data-testid="recipe-cook-input"
              type="number"
              min="0"
              class="textbox add-edit-modal__number-input"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="recipe-total">Total (min)</label>
            <input
              id="recipe-total"
              v-model="form.total_time_minutes"
              data-testid="recipe-total-input"
              type="number"
              min="0"
              class="textbox add-edit-modal__number-input"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="recipe-servings">Servings</label>
            <input
              id="recipe-servings"
              v-model="form.servings"
              data-testid="recipe-servings-input"
              type="number"
              min="1"
              class="textbox add-edit-modal__number-input"
              required
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="recipe-rating">Rating</label>
            <input
              id="recipe-rating"
              v-model="form.rating"
              data-testid="recipe-rating-input"
              type="number"
              min="1"
              max="5"
              class="textbox add-edit-modal__number-input"
            />
          </div>
        </div>

        <!-- tags -->
        <div class="add-edit-modal__form-item">
          <label for="recipe-tags">Tags (comma-separated)</label>
          <input
            id="recipe-tags"
            v-model="form.tags"
            data-testid="recipe-tags-input"
            type="text"
            class="textbox"
          />
        </div>

        <!-- source -->
        <div class="add-edit-modal__form-row">
          <div class="add-edit-modal__form-item">
            <label for="recipe-source-url">Source URL</label>
            <input
              id="recipe-source-url"
              v-model="form.source_url"
              data-testid="recipe-source-url-input"
              type="url"
              class="textbox"
            />
          </div>
          <div class="add-edit-modal__form-item">
            <label for="recipe-source-name">Source Name</label>
            <input
              id="recipe-source-name"
              v-model="form.source_name"
              data-testid="recipe-source-name-input"
              type="text"
              class="textbox"
            />
          </div>
        </div>

        <!-- ingredients -->
        <div class="add-edit-modal__form-item recipe-modal__ingredients">
          <div class="recipe-modal__ingredients-header">
            <label>Ingredients</label>
            <button
              type="button"
              class="button button--small"
              data-testid="recipe-add-ingredient-button"
              @click="addIngredient"
            >
              <span class="button__text">+ Add Ingredient</span>
            </button>
          </div>

          <div
            v-for="(ing, idx) in form.ingredients"
            :key="idx"
            class="recipe-modal__ingredient-row"
            data-testid="recipe-ingredient-row"
          >
            <input
              v-model="ing.quantity"
              type="number"
              step="any"
              min="0"
              class="textbox recipe-modal__ingredient-quantity"
              placeholder="Qty"
              :data-testid="`recipe-ingredient-quantity-${idx}`"
            />
            <NeuSelect
              :model-value="ing.unit ?? ''"
              :options="unitOptions"
              :data-testid="`recipe-ingredient-unit-${idx}`"
              @update:model-value="ing.unit = $event || null"
            />
            <input
              v-model="ing.item"
              type="text"
              class="textbox recipe-modal__ingredient-item"
              placeholder="Ingredient"
              required
              :data-testid="`recipe-ingredient-item-${idx}`"
            />
            <input
              v-model="ing.prep_note"
              type="text"
              class="textbox recipe-modal__ingredient-prep"
              placeholder="Prep (e.g. diced)"
              :data-testid="`recipe-ingredient-prep-${idx}`"
            />
            <button
              type="button"
              class="button button--danger button--small"
              :data-testid="`recipe-ingredient-remove-${idx}`"
              @click="removeIngredient(idx)"
            >
              <span class="button__text button__text--danger">×</span>
            </button>
          </div>

          <p
            v-if="form.ingredients.length === 0"
            class="recipe-modal__empty-ingredients"
          >
            Add at least one ingredient.
          </p>
        </div>

        <!-- instructions -->
        <div class="add-edit-modal__form-item">
          <label for="recipe-instructions">Instructions</label>
          <textarea
            id="recipe-instructions"
            v-model="form.instructions"
            data-testid="recipe-instructions-input"
            rows="6"
            class="textbox"
            required
          ></textarea>
        </div>

        <!-- notes -->
        <div class="add-edit-modal__form-item">
          <label for="recipe-notes">Notes</label>
          <textarea
            id="recipe-notes"
            v-model="form.notes"
            data-testid="recipe-notes-input"
            rows="2"
            class="textbox"
          ></textarea>
        </div>

        <div class="add-edit-modal__form-buttons">
          <button
            type="submit"
            data-testid="recipe-submit-button"
            class="button"
            :disabled="!canSubmit"
          >
            <span class="button__text">{{ editData ? 'Update' : 'Add' }} Recipe</span>
          </button>
          <button
            type="button"
            data-testid="recipe-cancel-button"
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
import { reactive, ref, watch, computed } from 'vue'
import type { Recipe, RecipeCreate, RecipeUpdate, RecipeIngredientCreate } from '@/api/client'
import AddEditModal from '@/components/AddEditModal.vue'
import NeuSelect from '@/components/NeuSelect.vue'

const props = defineProps<{
  visible: boolean
  editData?: Recipe | null
}>()

const emit = defineEmits<{
  close: []
  create: [data: RecipeCreate]
  update: [id: number, data: RecipeUpdate]
}>()

const nameInput = ref<HTMLInputElement | null>(null)

const cuisineOptions = [
  { value: '', label: '—' },
  { value: 'american', label: 'American' },
  { value: 'italian', label: 'Italian' },
  { value: 'mexican', label: 'Mexican' },
  { value: 'asian', label: 'Asian' },
  { value: 'indian', label: 'Indian' },
  { value: 'mediterranean', label: 'Mediterranean' },
  { value: 'french', label: 'French' },
  { value: 'other', label: 'Other' },
]

const mealTypeOptions = [
  { value: '', label: '—' },
  { value: 'breakfast', label: 'Breakfast' },
  { value: 'lunch', label: 'Lunch' },
  { value: 'dinner', label: 'Dinner' },
  { value: 'snack', label: 'Snack' },
  { value: 'dessert', label: 'Dessert' },
  { value: 'side', label: 'Side' },
  { value: 'sauce', label: 'Sauce' },
  { value: 'drink', label: 'Drink' },
]

const difficultyOptions = [
  { value: '', label: '—' },
  { value: 'easy', label: 'Easy' },
  { value: 'medium', label: 'Medium' },
  { value: 'hard', label: 'Hard' },
]

const unitOptions = [
  { value: '', label: '—' },
  { value: 'cup', label: 'cup' },
  { value: 'tbsp', label: 'tbsp' },
  { value: 'tsp', label: 'tsp' },
  { value: 'oz', label: 'oz' },
  { value: 'fl_oz', label: 'fl oz' },
  { value: 'lb', label: 'lb' },
  { value: 'g', label: 'g' },
  { value: 'kg', label: 'kg' },
  { value: 'ml', label: 'ml' },
  { value: 'l', label: 'l' },
  { value: 'pinch', label: 'pinch' },
  { value: 'dash', label: 'dash' },
  { value: 'clove', label: 'clove' },
  { value: 'slice', label: 'slice' },
  { value: 'can', label: 'can' },
  { value: 'package', label: 'package' },
  { value: 'piece', label: 'piece' },
  { value: 'whole', label: 'whole' },
  { value: 'to_taste', label: 'to taste' },
]

interface IngredientFormRow {
  quantity: string | number | null
  unit: string | null
  item: string
  prep_note: string
}

function emptyIngredient(): IngredientFormRow {
  return { quantity: '', unit: '', item: '', prep_note: '' }
}

function createEmptyForm() {
  return {
    name: '',
    description: '',
    source_url: '',
    source_name: '',
    prep_time_minutes: '',
    cook_time_minutes: '',
    total_time_minutes: '',
    servings: '4',
    difficulty: '',
    cuisine: '',
    meal_type: '',
    tags: '',
    instructions: '',
    notes: '',
    rating: '',
    ingredients: [emptyIngredient()] as IngredientFormRow[],
  }
}

const form = reactive(createEmptyForm())

const canSubmit = computed(() => {
  return form.name.trim() !== '' && form.instructions.trim() !== '' && form.ingredients.some((i) => i.item.trim() !== '')
})

watch(
  () => props.visible,
  (val) => {
    if (val && props.editData) {
      const r = props.editData
      form.name = r.name
      form.description = r.description ?? ''
      form.source_url = r.source_url ?? ''
      form.source_name = r.source_name ?? ''
      form.prep_time_minutes = r.prep_time_minutes != null ? String(r.prep_time_minutes) : ''
      form.cook_time_minutes = r.cook_time_minutes != null ? String(r.cook_time_minutes) : ''
      form.total_time_minutes = r.total_time_minutes != null ? String(r.total_time_minutes) : ''
      form.servings = String(r.servings)
      form.difficulty = r.difficulty ?? ''
      form.cuisine = r.cuisine ?? ''
      form.meal_type = r.meal_type ?? ''
      form.tags = (r.tags ?? []).join(', ')
      form.instructions = r.instructions
      form.notes = r.notes ?? ''
      form.rating = r.rating != null ? String(r.rating) : ''
      form.ingredients = r.ingredients.map((ing) => ({
        quantity: ing.quantity != null ? String(ing.quantity) : '',
        unit: ing.unit ?? '',
        item: ing.item,
        prep_note: ing.prep_note ?? '',
      }))
      if (form.ingredients.length === 0) form.ingredients.push(emptyIngredient())
    } else if (val && !props.editData) {
      Object.assign(form, createEmptyForm())
    }
  }
)

function resetForm() {
  Object.assign(form, createEmptyForm())
}

function handleModalClose() {
  resetForm()
  emit('close')
}

function addIngredient() {
  form.ingredients.push(emptyIngredient())
}

function removeIngredient(idx: number) {
  form.ingredients.splice(idx, 1)
  if (form.ingredients.length === 0) form.ingredients.push(emptyIngredient())
}

function buildIngredients(): RecipeIngredientCreate[] {
  return form.ingredients
    .filter((i) => i.item.trim() !== '')
    .map((i, idx) => ({
      position: idx,
      quantity: i.quantity === '' || i.quantity === null ? null : Number(i.quantity),
      unit: i.unit || null,
      item: i.item.trim(),
      prep_note: i.prep_note.trim() || null,
      is_optional: false,
      ingredient_group: null,
    }))
}

function buildPayload() {
  const tags = form.tags
    .split(',')
    .map((t) => t.trim())
    .filter(Boolean)
  const emptyVal = props.editData ? null : undefined
  return {
    name: form.name.trim(),
    description: form.description.trim() || emptyVal,
    source_url: form.source_url.trim() || emptyVal,
    source_name: form.source_name.trim() || emptyVal,
    prep_time_minutes: form.prep_time_minutes ? Number(form.prep_time_minutes) : emptyVal,
    cook_time_minutes: form.cook_time_minutes ? Number(form.cook_time_minutes) : emptyVal,
    total_time_minutes: form.total_time_minutes ? Number(form.total_time_minutes) : emptyVal,
    servings: form.servings ? Number(form.servings) : 4,
    difficulty: form.difficulty || emptyVal,
    cuisine: form.cuisine || emptyVal,
    meal_type: form.meal_type || emptyVal,
    tags: tags.length > 0 ? tags : emptyVal,
    instructions: form.instructions,
    notes: form.notes.trim() || emptyVal,
    rating: form.rating ? Number(form.rating) : emptyVal,
    ingredients: buildIngredients(),
  }
}

function handleSubmit(handleSuccess: () => void) {
  if (!canSubmit.value) return
  const payload = buildPayload()
  if (props.editData) {
    emit('update', props.editData.id, payload as RecipeUpdate)
  } else {
    emit('create', payload as RecipeCreate)
  }
  handleSuccess()
}
</script>

<style scoped>
.recipe-modal__ingredients-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-xs);
}

.recipe-modal__ingredient-row {
  display: grid;
  grid-template-columns: 80px 100px 1fr 1fr auto;
  gap: var(--space-xs);
  margin-bottom: var(--space-3xs);
  align-items: center;
}

.recipe-modal__ingredient-quantity {
  text-align: right;
}

.recipe-modal__empty-ingredients {
  color: var(--clr-gray-500);
  font-style: italic;
  font-size: var(--fs-300);
  margin-top: var(--space-xs);
}
</style>
