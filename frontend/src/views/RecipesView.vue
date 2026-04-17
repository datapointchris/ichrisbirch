<template>
  <div>
    <AppSubnav :links="subnavLinks" />

    <!-- Filter Bar -->
    <div class="grid grid--one-column grid--tight">
      <div class="task-layout__info">
        <NeuSelect
          :model-value="store.cuisineFilter"
          :options="cuisineFilterOptions"
          data-testid="recipe-cuisine-filter"
          @update:model-value="store.setCuisineFilter($event)"
        />
        <NeuSelect
          :model-value="store.mealTypeFilter"
          :options="mealTypeFilterOptions"
          data-testid="recipe-meal-type-filter"
          @update:model-value="store.setMealTypeFilter($event)"
        />
        <NeuSelect
          :model-value="store.difficultyFilter"
          :options="difficultyFilterOptions"
          data-testid="recipe-difficulty-filter"
          @update:model-value="store.setDifficultyFilter($event)"
        />
        <span class="recipes__count">{{ store.sortedRecipes.length }} recipes</span>
      </div>
    </div>

    <div class="add-item-wrapper">
      <button
        data-testid="recipe-add-button"
        class="button"
        @click="showModal = true"
      >
        <span class="button__text">Add Recipe</span>
      </button>
    </div>

    <!-- Search Mode Toggle -->
    <div class="grid grid--one-column grid--tight">
      <div class="recipes__search-mode">
        <button
          type="button"
          class="button"
          :class="{ 'button--active': searchMode === 'name' }"
          data-testid="recipe-search-mode-name"
          @click="searchMode = 'name'"
        >
          <span class="button__text">Name / Tag Search</span>
        </button>
        <button
          type="button"
          class="button"
          :class="{ 'button--active': searchMode === 'ingredients' }"
          data-testid="recipe-search-mode-ingredients"
          @click="searchMode = 'ingredients'"
        >
          <span class="button__text">Ingredient Search</span>
        </button>
      </div>
    </div>

    <!-- Name / Tag Search Form -->
    <div
      v-if="searchMode === 'name'"
      class="grid grid--one-column grid--tight"
    >
      <div class="grid__item">
        <form
          class="recipes__search"
          @submit.prevent="handleSearch"
        >
          <input
            v-model="searchInput"
            type="text"
            class="textbox"
            placeholder="Search recipe names, tags, or instructions..."
            data-testid="recipe-search-input"
          />
          <button
            type="submit"
            class="button"
            data-testid="recipe-search-button"
          >
            <span class="button__text">Search</span>
          </button>
          <button
            v-if="store.isSearchActive"
            type="button"
            class="button button--danger"
            @click="handleClearSearch"
          >
            <span class="button__text button__text--danger">Clear</span>
          </button>
        </form>
      </div>
    </div>

    <!-- Ingredient Search Form -->
    <div
      v-if="searchMode === 'ingredients'"
      class="grid grid--one-column grid--tight"
    >
      <div class="grid__item">
        <form
          class="recipes__search"
          @submit.prevent="handleIngredientSearch"
        >
          <input
            v-model="ingredientInput"
            type="text"
            class="textbox"
            placeholder="Ingredients you have (comma-separated)..."
            data-testid="recipe-ingredient-search-input"
          />
          <NeuSelect
            :model-value="ingredientMatch"
            :options="matchOptions"
            data-testid="recipe-ingredient-match-select"
            @update:model-value="ingredientMatch = $event as 'any' | 'all'"
          />
          <button
            type="submit"
            class="button"
            data-testid="recipe-ingredient-search-button"
          >
            <span class="button__text">Find Recipes</span>
          </button>
          <button
            v-if="store.ingredientSearchActive"
            type="button"
            class="button button--danger"
            @click="handleClearSearch"
          >
            <span class="button__text button__text--danger">Clear</span>
          </button>
        </form>
      </div>
    </div>

    <!-- Ingredient Search Results -->
    <div
      v-if="store.ingredientSearchActive"
      class="grid grid--one-column-full"
    >
      <div class="grid__item">
        <div
          v-if="store.ingredientSearchResults.length === 0"
          class="recipes__empty"
        >
          No recipes match those ingredients.
        </div>
        <template
          v-for="result in store.ingredientSearchResults"
          :key="result.recipe.id"
        >
          <div
            class="recipes__row recipes__match-row"
            data-testid="recipe-match-item"
          >
            <span class="recipes__title">{{ result.recipe.name }}</span>
            <span class="recipes__coverage">{{ result.coverage }} of {{ result.total_ingredients }} ingredients</span>
            <span class="recipes__actions">
              <ActionButton
                icon="fa-solid fa-eye"
                title="View recipe"
                @click="goToDetail(result.recipe.id)"
              />
            </span>
          </div>
        </template>
      </div>
    </div>

    <!-- Recipe Table -->
    <div
      v-else
      class="grid grid--one-column-full"
    >
      <div class="grid__item">
        <div
          v-if="store.loading"
          class="recipes__empty"
        >
          Loading...
        </div>
        <template v-else>
          <div class="recipes__header">
            <span
              class="recipes__sortable"
              @click="store.setSort('name')"
              >Name<span class="recipes__sort-indicator">{{ sortIndicator('name') }}</span></span
            >
            <span
              class="recipes__sortable"
              @click="store.setSort('cuisine')"
              >Cuisine<span class="recipes__sort-indicator">{{ sortIndicator('cuisine') }}</span></span
            >
            <span
              class="recipes__sortable"
              @click="store.setSort('total_time')"
              >Time<span class="recipes__sort-indicator">{{ sortIndicator('total_time') }}</span></span
            >
            <span
              class="recipes__sortable"
              @click="store.setSort('times_made')"
              >Made<span class="recipes__sort-indicator">{{ sortIndicator('times_made') }}</span></span
            >
            <span
              class="recipes__sortable"
              @click="store.setSort('rating')"
              >Rating<span class="recipes__sort-indicator">{{ sortIndicator('rating') }}</span></span
            >
            <span>Actions</span>
          </div>

          <template v-if="store.sortedRecipes.length === 0">
            <div class="recipes__empty">No recipes match the selected filters.</div>
          </template>

          <template
            v-for="recipe in store.sortedRecipes"
            :key="recipe.id"
          >
            <div
              data-testid="recipe-item"
              class="recipes__row"
            >
              <span
                class="recipes__title"
                :title="recipe.name"
                >{{ recipe.name }}</span
              >
              <span>{{ recipe.cuisine ?? '' }}</span>
              <span>{{ recipe.total_time_minutes != null ? `${recipe.total_time_minutes}m` : '' }}</span>
              <span>{{ recipe.times_made }}×</span>
              <span>{{ recipe.rating ?? '' }}</span>
              <span class="recipes__actions">
                <ActionButton
                  icon="fa-solid fa-eye"
                  title="View details"
                  @click="goToDetail(recipe.id)"
                />
                <ActionButton
                  data-testid="recipe-mark-made-button"
                  icon="fa-solid fa-check"
                  variant="success"
                  title="Mark as made"
                  @click="handleMarkMade(recipe.id)"
                />
                <ActionButton
                  data-testid="recipe-edit-button"
                  icon="fa-solid fa-pen-to-square"
                  variant="warning"
                  title="Edit recipe"
                  @click="openEdit(recipe)"
                />
                <ActionButton
                  data-testid="recipe-delete-button"
                  icon="fa-regular fa-trash-can"
                  variant="danger"
                  title="Delete recipe"
                  @click="handleDelete(recipe.id)"
                />
              </span>
            </div>
          </template>
        </template>
      </div>
    </div>

    <AddEditRecipeModal
      :visible="showModal"
      :edit-data="editTarget"
      @close="closeModal"
      @create="handleCreate"
      @update="handleUpdate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppSubnav from '@/components/AppSubnav.vue'
import ActionButton from '@/components/ActionButton.vue'
import NeuSelect from '@/components/NeuSelect.vue'
import AddEditRecipeModal from '@/components/recipes/AddEditRecipeModal.vue'
import { useRecipesStore } from '@/stores/recipes'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import type { Recipe } from '@/api/client'
import { RECIPES_SUBNAV } from '@/config/subnavLinks'

const subnavLinks = RECIPES_SUBNAV
const router = useRouter()
const store = useRecipesStore()
const { show: notify } = useNotifications()

const showModal = ref(false)
const editTarget = ref<Recipe | null>(null)
const searchInput = ref('')
const ingredientInput = ref('')
const ingredientMatch = ref<'any' | 'all'>('any')
const searchMode = ref<'name' | 'ingredients'>('name')

const cuisineFilterOptions = [
  { value: 'all', label: 'All Cuisines' },
  { value: 'american', label: 'American' },
  { value: 'italian', label: 'Italian' },
  { value: 'mexican', label: 'Mexican' },
  { value: 'asian', label: 'Asian' },
  { value: 'indian', label: 'Indian' },
  { value: 'mediterranean', label: 'Mediterranean' },
  { value: 'french', label: 'French' },
  { value: 'other', label: 'Other' },
]

const mealTypeFilterOptions = [
  { value: 'all', label: 'All Meals' },
  { value: 'breakfast', label: 'Breakfast' },
  { value: 'lunch', label: 'Lunch' },
  { value: 'dinner', label: 'Dinner' },
  { value: 'snack', label: 'Snack' },
  { value: 'dessert', label: 'Dessert' },
  { value: 'side', label: 'Side' },
  { value: 'sauce', label: 'Sauce' },
  { value: 'drink', label: 'Drink' },
]

const difficultyFilterOptions = [
  { value: 'all', label: 'All Difficulties' },
  { value: 'easy', label: 'Easy' },
  { value: 'medium', label: 'Medium' },
  { value: 'hard', label: 'Hard' },
]

const matchOptions = [
  { value: 'any', label: 'Any ingredient' },
  { value: 'all', label: 'All ingredients' },
]

onMounted(() => {
  store.fetchAll()
})

function sortIndicator(field: string): string {
  if (store.sortField !== field) return ''
  return store.sortDirection === 'asc' ? ' \u25B2' : ' \u25BC'
}

function goToDetail(id: number) {
  router.push(`/recipes/${id}`)
}

async function handleDelete(id: number) {
  const recipe = store.recipes.find((r) => r.id === id)
  const label = recipe ? recipe.name : `Recipe ${id}`
  try {
    await store.remove(id)
    notify(`${label} deleted`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Delete failed: ${detail}`, 'error')
  }
}

async function handleMarkMade(id: number) {
  try {
    const updated = await store.markMade(id)
    notify(`${updated.name} marked as made (${updated.times_made}×)`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Mark as made failed: ${detail}`, 'error')
  }
}

function openEdit(recipe: Recipe) {
  editTarget.value = recipe
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editTarget.value = null
}

async function handleCreate(data: Parameters<typeof store.create>[0]) {
  try {
    await store.create(data)
    notify(`${data.name} added`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Add failed: ${detail}`, 'error')
  }
}

async function handleUpdate(id: number, data: Parameters<typeof store.update>[1]) {
  const name = store.recipes.find((r) => r.id === id)?.name ?? 'Recipe'
  try {
    await store.update(id, data)
    notify(`${name} updated`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Update failed: ${detail}`, 'error')
  }
}

async function handleSearch() {
  if (!searchInput.value.trim()) return
  try {
    await store.search(searchInput.value.trim())
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Search failed: ${detail}`, 'error')
  }
}

async function handleIngredientSearch() {
  const terms = ingredientInput.value
    .split(',')
    .map((t) => t.trim())
    .filter(Boolean)
  if (terms.length === 0) return
  try {
    await store.searchByIngredients(terms, ingredientMatch.value)
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Ingredient search failed: ${detail}`, 'error')
  }
}

async function handleClearSearch() {
  searchInput.value = ''
  ingredientInput.value = ''
  await store.clearSearch()
}
</script>

<style scoped>
.recipes__search {
  display: flex;
  gap: var(--space-xs);
  align-items: center;
}

.recipes__search .textbox {
  flex: 1;
}

.recipes__search-mode {
  display: flex;
  gap: var(--space-xs);
  justify-content: center;
  margin-bottom: var(--space-xs);
}

.recipes__count {
  font-size: var(--fs-300);
  color: var(--clr-gray-400);
  align-self: center;
}

.recipes__match-row {
  grid-template-columns: 4fr 3fr 1fr !important;
}

.recipes__coverage {
  color: var(--clr-accent-light);
  font-size: var(--fs-300);
}
</style>
