<template>
  <div>
    <AppSubnav :links="subnavLinks" />

    <div
      v-if="loading"
      class="recipes__empty"
    >
      Loading...
    </div>

    <div
      v-else-if="!recipe"
      class="recipes__empty"
    >
      Recipe not found.
    </div>

    <div
      v-else
      class="recipe-detail"
      data-testid="recipe-detail"
    >
      <div class="recipe-detail__header">
        <button
          type="button"
          class="button"
          data-testid="recipe-detail-back"
          @click="$router.push('/recipes')"
        >
          <span class="button__text">← Back</span>
        </button>
        <h1 class="recipe-detail__title">{{ recipe.name }}</h1>
        <div class="recipe-detail__header-actions">
          <button
            type="button"
            class="button"
            data-testid="recipe-detail-mark-made"
            @click="handleMarkMade"
          >
            <span class="button__text">Mark as Made</span>
          </button>
          <button
            type="button"
            class="button button--warning"
            data-testid="recipe-detail-edit"
            @click="showModal = true"
          >
            <span class="button__text">Edit</span>
          </button>
        </div>
      </div>

      <p
        v-if="recipe.description"
        class="recipe-detail__description"
      >
        {{ recipe.description }}
      </p>

      <div class="recipe-detail__meta">
        <span v-if="recipe.cuisine"><strong>Cuisine:</strong> {{ recipe.cuisine }}</span>
        <span v-if="recipe.meal_type"><strong>Meal:</strong> {{ recipe.meal_type }}</span>
        <span v-if="recipe.difficulty"><strong>Difficulty:</strong> {{ recipe.difficulty }}</span>
        <span v-if="recipe.prep_time_minutes != null"><strong>Prep:</strong> {{ recipe.prep_time_minutes }}m</span>
        <span v-if="recipe.cook_time_minutes != null"><strong>Cook:</strong> {{ recipe.cook_time_minutes }}m</span>
        <span v-if="recipe.total_time_minutes != null"><strong>Total:</strong> {{ recipe.total_time_minutes }}m</span>
        <span><strong>Made:</strong> {{ recipe.times_made }}×</span>
        <span v-if="recipe.rating"><strong>Rating:</strong> {{ recipe.rating }}/5</span>
      </div>

      <div class="recipe-detail__body">
        <section class="recipe-detail__ingredients-section">
          <div class="recipe-detail__section-header">
            <h2>Ingredients</h2>
            <div class="recipe-detail__scaler">
              <label for="scaler">Servings:</label>
              <input
                id="scaler"
                v-model.number="currentServings"
                type="number"
                min="1"
                step="1"
                class="textbox recipe-detail__scaler-input"
                data-testid="recipe-detail-servings-input"
                @change="handleServingsChange"
              />
              <span
                v-if="currentServings !== recipe.servings"
                class="recipe-detail__scaler-note"
                >(scaled from {{ recipe.servings }})</span
              >
            </div>
          </div>
          <ul
            class="recipe-detail__ingredients"
            data-testid="recipe-detail-ingredients"
          >
            <li
              v-for="ing in recipe.ingredients"
              :key="ing.id"
              class="recipe-detail__ingredient"
              data-testid="recipe-detail-ingredient"
            >
              <span class="recipe-detail__qty">{{ displayQuantity(ing) }}</span>
              <span class="recipe-detail__unit">{{ formatUnit(ing.unit) }}</span>
              <span class="recipe-detail__item">{{ ing.item }}</span>
              <span
                v-if="ing.prep_note"
                class="recipe-detail__prep"
                >, {{ ing.prep_note }}</span
              >
            </li>
          </ul>
        </section>

        <section class="recipe-detail__instructions-section">
          <h2>Instructions</h2>
          <div class="recipe-detail__instructions">
            {{ recipe.instructions }}
          </div>
        </section>
      </div>

      <section
        v-if="recipe.tags && recipe.tags.length > 0"
        class="recipe-detail__tags"
      >
        <span
          v-for="tag in recipe.tags"
          :key="tag"
          class="recipe-detail__tag"
          >{{ tag }}</span
        >
      </section>

      <section
        v-if="recipe.notes"
        class="recipe-detail__notes"
      >
        <h3>Notes</h3>
        <p>{{ recipe.notes }}</p>
      </section>

      <section
        v-if="recipe.source_url"
        class="recipe-detail__source"
      >
        <a
          :href="recipe.source_url"
          target="_blank"
          rel="noopener"
          >{{ recipe.source_name || 'Source' }}</a
        >
      </section>
    </div>

    <AddEditRecipeModal
      :visible="showModal"
      :edit-data="recipe"
      @close="showModal = false"
      @update="handleUpdate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppSubnav from '@/components/AppSubnav.vue'
import AddEditRecipeModal from '@/components/recipes/AddEditRecipeModal.vue'
import { useRecipesStore } from '@/stores/recipes'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import type { Recipe, RecipeIngredient, RecipeUpdate } from '@/api/client'
import { RECIPES_SUBNAV } from '@/config/subnavLinks'

const subnavLinks = RECIPES_SUBNAV
const route = useRoute()
const store = useRecipesStore()
const { show: notify } = useNotifications()

const recipe = ref<Recipe | null>(null)
const loading = ref(false)
const currentServings = ref(4)
const showModal = ref(false)

const recipeId = () => Number(route.params.id)

async function loadRecipe(servings?: number) {
  loading.value = true
  try {
    const data = await store.fetchOne(recipeId(), servings)
    recipe.value = data
    if (servings === undefined) {
      currentServings.value = data.servings
    }
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to load recipe: ${detail}`, 'error')
  } finally {
    loading.value = false
  }
}

onMounted(() => loadRecipe())

watch(
  () => route.params.id,
  () => {
    if (route.params.id) loadRecipe()
  }
)

async function handleServingsChange() {
  if (currentServings.value < 1) currentServings.value = 1
  await loadRecipe(currentServings.value)
}

async function handleMarkMade() {
  if (!recipe.value) return
  try {
    const updated = await store.markMade(recipe.value.id)
    recipe.value = { ...updated, ingredients: recipe.value.ingredients }
    notify(`Marked as made (${updated.times_made}×)`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Mark as made failed: ${detail}`, 'error')
  }
}

async function handleUpdate(id: number, data: RecipeUpdate) {
  try {
    await store.update(id, data)
    await loadRecipe(currentServings.value)
    notify('Recipe updated', 'success')
    showModal.value = false
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Update failed: ${detail}`, 'error')
  }
}

function displayQuantity(ing: RecipeIngredient): string {
  const qty = ing.scaled_quantity ?? ing.quantity
  if (qty === null || qty === undefined) return ''
  // Prefer fractions for readability on common values
  if (qty === 0.25) return '1/4'
  if (qty === 0.5) return '1/2'
  if (qty === 0.75) return '3/4'
  if (qty === 0.125) return '1/8'
  if (qty === 0.375) return '3/8'
  if (qty === 0.625) return '5/8'
  if (qty === 0.875) return '7/8'
  // Strip trailing .0 for whole numbers
  if (Number.isInteger(qty)) return String(qty)
  return String(Math.round(qty * 100) / 100)
}

function formatUnit(unit: string | null): string {
  if (!unit) return ''
  if (unit === 'to_taste') return 'to taste'
  if (unit === 'fl_oz') return 'fl oz'
  return unit
}
</script>

<style scoped>
.recipe-detail {
  display: flex;
  flex-direction: column;
  gap: var(--space-m);
  padding: var(--space-m);
}

.recipe-detail__header {
  display: flex;
  align-items: center;
  gap: var(--space-s);
  flex-wrap: wrap;
}

.recipe-detail__title {
  flex: 1;
  margin: 0;
  font-size: var(--fs-700);
}

.recipe-detail__header-actions {
  display: flex;
  gap: var(--space-xs);
}

.recipe-detail__description {
  margin: 0;
  font-size: var(--fs-400);
  color: var(--clr-text);
  font-style: italic;
}

.recipe-detail__meta {
  display: flex;
  gap: var(--space-m);
  flex-wrap: wrap;
  padding: var(--space-s);
  box-shadow: var(--floating-box);
  border-radius: var(--border-radius);
  font-size: var(--fs-300);
  text-transform: capitalize;
}

.recipe-detail__body {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: var(--space-m);
}

@media (max-width: 800px) {
  .recipe-detail__body {
    grid-template-columns: 1fr;
  }
}

.recipe-detail__ingredients-section,
.recipe-detail__instructions-section {
  padding: var(--space-s);
  box-shadow: var(--floating-box);
  border-radius: var(--border-radius);
}

.recipe-detail__section-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: var(--space-s);
}

.recipe-detail__scaler {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: var(--fs-300);
}

.recipe-detail__scaler-input {
  width: 60px;
  text-align: center;
}

.recipe-detail__scaler-note {
  color: var(--clr-accent-light);
  font-style: italic;
}

.recipe-detail__ingredients {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.recipe-detail__ingredient {
  display: grid;
  grid-template-columns: 60px 80px 1fr auto;
  gap: var(--space-xs);
  align-items: baseline;
  padding-block: var(--space-3xs);
}

.recipe-detail__qty {
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

.recipe-detail__unit {
  color: var(--clr-gray-400);
  font-size: var(--fs-300);
}

.recipe-detail__prep {
  color: var(--clr-gray-400);
  font-style: italic;
  font-size: var(--fs-300);
}

.recipe-detail__instructions {
  white-space: pre-wrap;
  line-height: 1.6;
  font-size: var(--fs-400);
}

.recipe-detail__tags {
  display: flex;
  gap: var(--space-xs);
  flex-wrap: wrap;
}

.recipe-detail__tag {
  padding: var(--space-3xs) var(--space-xs);
  background-color: var(--clr-primary);
  border-radius: var(--button-border-radius);
  font-size: var(--fs-300);
  color: var(--clr-accent-light);
}

.recipe-detail__notes {
  padding: var(--space-s);
  box-shadow: var(--floating-box);
  border-radius: var(--border-radius);
}

.recipe-detail__source a {
  color: var(--clr-accent-light);
  text-decoration: underline;
}
</style>
