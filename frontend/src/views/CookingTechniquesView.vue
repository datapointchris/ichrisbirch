<template>
  <div>
    <AppSubnav :links="subnavLinks" />

    <!-- Filter Bar -->
    <div class="grid grid--one-column grid--tight">
      <div class="task-layout__info">
        <NeuSelect
          :model-value="store.categoryFilter"
          :options="categoryFilterOptions"
          data-testid="cooking-technique-category-filter"
          @update:model-value="store.setCategoryFilter($event)"
        />
        <span class="cooking-techniques__count">{{ store.sortedTechniques.length }} techniques</span>
      </div>
    </div>

    <div class="add-item-wrapper">
      <button
        data-testid="cooking-technique-add-button"
        class="button"
        @click="showModal = true"
      >
        <span class="button__text">Add Technique</span>
      </button>
    </div>

    <!-- Search Form -->
    <div class="grid grid--one-column grid--tight">
      <div class="grid__item">
        <form
          class="cooking-techniques__search"
          @submit.prevent="handleSearch"
        >
          <input
            v-model="searchInput"
            type="text"
            class="textbox"
            placeholder="Search name, summary, body, or tags..."
            data-testid="cooking-technique-search-input"
          />
          <button
            type="submit"
            class="button"
            data-testid="cooking-technique-search-button"
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

    <!-- Technique Table -->
    <div class="grid grid--one-column-full">
      <div class="grid__item">
        <div
          v-if="store.loading"
          class="cooking-techniques__empty"
        >
          Loading...
        </div>
        <template v-else>
          <div class="cooking-techniques__header">
            <span
              class="cooking-techniques__sortable"
              @click="store.setSort('name')"
              >Name<span class="cooking-techniques__sort-indicator">{{ sortIndicator('name') }}</span></span
            >
            <span
              class="cooking-techniques__sortable"
              @click="store.setSort('category')"
              >Category<span class="cooking-techniques__sort-indicator">{{ sortIndicator('category') }}</span></span
            >
            <span
              class="cooking-techniques__sortable"
              @click="store.setSort('rating')"
              >Rating<span class="cooking-techniques__sort-indicator">{{ sortIndicator('rating') }}</span></span
            >
            <span>Actions</span>
          </div>

          <template v-if="store.sortedTechniques.length === 0">
            <div class="cooking-techniques__empty">No techniques match the selected filters.</div>
          </template>

          <template
            v-for="technique in store.sortedTechniques"
            :key="technique.id"
          >
            <div
              data-testid="cooking-technique-item"
              class="cooking-techniques__row"
            >
              <span
                class="cooking-techniques__title"
                :title="technique.summary"
                >{{ technique.name }}</span
              >
              <span class="cooking-techniques__category">{{ categoryLabel(technique.category) }}</span>
              <span>{{ technique.rating ?? '' }}</span>
              <span class="cooking-techniques__actions">
                <ActionButton
                  data-testid="cooking-technique-view-button"
                  icon="fa-solid fa-eye"
                  title="View details"
                  @click="goToDetail(technique.slug)"
                />
                <ActionButton
                  data-testid="cooking-technique-edit-button"
                  icon="fa-solid fa-pen-to-square"
                  variant="warning"
                  title="Edit"
                  @click="openEdit(technique)"
                />
                <ActionButton
                  data-testid="cooking-technique-delete-button"
                  icon="fa-regular fa-trash-can"
                  variant="danger"
                  title="Delete"
                  @click="handleDelete(technique.id)"
                />
              </span>
            </div>
          </template>
        </template>
      </div>
    </div>

    <AddEditCookingTechniqueModal
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
import AddEditCookingTechniqueModal from '@/components/recipes/AddEditCookingTechniqueModal.vue'
import { useCookingTechniquesStore } from '@/stores/cookingTechniques'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import type { CookingTechnique } from '@/api/client'
import { RECIPES_SUBNAV } from '@/config/subnavLinks'

const subnavLinks = RECIPES_SUBNAV
const router = useRouter()
const store = useCookingTechniquesStore()
const { show: notify } = useNotifications()

const showModal = ref(false)
const editTarget = ref<CookingTechnique | null>(null)
const searchInput = ref('')

const categoryFilterOptions = [
  { value: 'all', label: 'All Categories' },
  { value: 'heat_application', label: 'Heat application' },
  { value: 'flavor_development', label: 'Flavor development' },
  { value: 'emulsion_and_texture', label: 'Emulsion & texture' },
  { value: 'preservation_and_pre_treatment', label: 'Preservation & pre-treatment' },
  { value: 'seasoning_and_finishing', label: 'Seasoning & finishing' },
  { value: 'dough_and_batter', label: 'Dough & batter' },
  { value: 'knife_work_and_prep', label: 'Knife work & prep' },
  { value: 'composition_and_ratio', label: 'Composition & ratio' },
  { value: 'equipment_technique', label: 'Equipment technique' },
]

const CATEGORY_LABELS: Record<string, string> = Object.fromEntries(
  categoryFilterOptions.filter((opt) => opt.value !== 'all').map((opt) => [opt.value, opt.label])
)

function categoryLabel(value: string): string {
  return CATEGORY_LABELS[value] ?? value
}

onMounted(() => {
  store.fetchAll()
})

function sortIndicator(field: string): string {
  if (store.sortField !== field) return ''
  return store.sortDirection === 'asc' ? ' ▲' : ' ▼'
}

function goToDetail(slug: string) {
  router.push(`/recipes/cooking-techniques/${slug}`)
}

async function handleDelete(id: number) {
  const technique = store.techniques.find((t) => t.id === id)
  const label = technique ? technique.name : `Technique ${id}`
  try {
    await store.remove(id)
    notify(`${label} deleted`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Delete failed: ${detail}`, 'error')
  }
}

function openEdit(technique: CookingTechnique) {
  editTarget.value = technique
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
  const name = store.techniques.find((t) => t.id === id)?.name ?? 'Technique'
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

async function handleClearSearch() {
  searchInput.value = ''
  await store.clearSearch()
}
</script>

<style scoped>
.cooking-techniques__search {
  display: flex;
  gap: var(--space-xs);
  align-items: center;
}

.cooking-techniques__search .textbox {
  flex: 1;
}

.cooking-techniques__count {
  font-size: var(--fs-300);
  color: var(--clr-gray-400);
  align-self: center;
}

.cooking-techniques__header,
.cooking-techniques__row {
  display: grid;
  grid-template-columns: 3fr 2fr 1fr auto;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-sm);
  align-items: center;
}

.cooking-techniques__header {
  font-weight: 600;
  border-bottom: 1px solid var(--clr-gray-300);
}

.cooking-techniques__row {
  box-shadow: var(--floating-box);
  border-radius: var(--border-radius);
  margin-bottom: var(--space-xs);
}

.cooking-techniques__title {
  font-weight: 600;
}

.cooking-techniques__category {
  font-size: var(--fs-300);
}

.cooking-techniques__actions {
  display: flex;
  gap: var(--space-xs);
  justify-content: flex-end;
}

.cooking-techniques__sortable {
  cursor: pointer;
  user-select: none;
}

.cooking-techniques__sort-indicator {
  font-size: var(--fs-200);
}

.cooking-techniques__empty {
  color: var(--clr-gray-500);
  font-style: italic;
  padding: var(--space-md);
  text-align: center;
}
</style>
