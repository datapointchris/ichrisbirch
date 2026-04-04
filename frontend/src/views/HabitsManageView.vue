<template>
  <div>
    <AppSubnav :links="subnavLinks" />

    <div
      v-if="store.loading"
      class="grid grid--one-column"
    >
      <div class="grid__item">Loading...</div>
    </div>

    <template v-else>
      <!-- Add buttons -->
      <div class="add-item-wrapper">
        <button
          data-testid="habit-add-button"
          class="button"
          @click="showHabitModal = true"
        >
          <span class="button__text">Add Habit</span>
        </button>
        <button
          data-testid="category-add-button"
          class="button"
          @click="showCategoryModal = true"
        >
          <span class="button__text">Add Category</span>
        </button>
      </div>

      <!-- Current Habits -->
      <div class="grid grid--one-column grid--tight">
        <div class="grid__item">
          <h3 class="habits-manage__section-title">Current Habits</h3>
          <div
            v-if="store.currentHabits.length === 0"
            class="habits-manage__empty"
          >
            No current habits.
          </div>
          <div
            v-for="habit in store.currentHabits"
            :key="habit.id"
            data-testid="habit-item"
            class="habits-manage__row"
          >
            <span>{{ habit.name }}</span>
            <span class="habits-manage__category-tag">{{ habit.category.name }}</span>
            <div class="habits-manage__actions">
              <button
                data-testid="habit-edit-button"
                class="button"
                @click="openEditHabit(habit)"
              >
                <span class="button__text">Edit</span>
              </button>
              <button
                data-testid="habit-hibernate-button"
                class="button"
                @click="handleHibernateHabit(habit.id)"
              >
                <span class="button__text">Hibernate</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Hibernating Habits -->
      <div
        v-if="store.hibernatingHabits.length > 0"
        class="grid grid--one-column grid--tight"
      >
        <div class="grid__item">
          <h3 class="habits-manage__section-title habits-manage__section-title--muted">Hibernating Habits</h3>
          <div
            v-for="habit in store.hibernatingHabits"
            :key="habit.id"
            data-testid="habit-item-hibernating"
            class="habits-manage__row habits-manage__row--muted"
          >
            <span>{{ habit.name }}</span>
            <span class="habits-manage__category-tag">{{ habit.category.name }}</span>
            <div class="habits-manage__actions">
              <button
                data-testid="habit-revive-button"
                class="button"
                @click="handleReviveHabit(habit.id)"
              >
                <span class="button__text">Revive</span>
              </button>
              <button
                data-testid="habit-delete-button"
                class="button--hidden"
                @click="handleDeleteHabit(habit.id)"
              >
                <i class="button-icon danger fa-regular fa-trash-can"></i>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Current Categories -->
      <div class="grid grid--one-column grid--tight">
        <div class="grid__item">
          <h3 class="habits-manage__section-title">Current Categories</h3>
          <div
            v-if="store.currentCategories.length === 0"
            class="habits-manage__empty"
          >
            No current categories.
          </div>
          <div
            v-for="cat in store.currentCategories"
            :key="cat.id"
            data-testid="category-item"
            class="habits-manage__row"
          >
            <span>{{ cat.name }}</span>
            <div class="habits-manage__actions">
              <button
                data-testid="category-edit-button"
                class="button"
                @click="openEditCategory(cat)"
              >
                <span class="button__text">Edit</span>
              </button>
              <button
                data-testid="category-hibernate-button"
                class="button"
                @click="handleHibernateCategory(cat.id)"
              >
                <span class="button__text">Hibernate</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Hibernating Categories -->
      <div
        v-if="store.hibernatingCategories.length > 0"
        class="grid grid--one-column grid--tight"
      >
        <div class="grid__item">
          <h3 class="habits-manage__section-title habits-manage__section-title--muted">Hibernating Categories</h3>
          <div
            v-for="cat in store.hibernatingCategories"
            :key="cat.id"
            data-testid="category-item-hibernating"
            class="habits-manage__row habits-manage__row--muted"
          >
            <span>{{ cat.name }}</span>
            <div class="habits-manage__actions">
              <button
                data-testid="category-revive-button"
                class="button"
                @click="handleReviveCategory(cat.id)"
              >
                <span class="button__text">Revive</span>
              </button>
              <button
                data-testid="category-delete-button"
                class="button--hidden"
                @click="handleDeleteCategory(cat.id)"
              >
                <i class="button-icon danger fa-regular fa-trash-can"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <AddEditHabitModal
      :visible="showHabitModal"
      :categories="store.currentCategories"
      :edit-data="editHabitTarget"
      @close="closeHabitModal"
      @create="handleCreateHabit"
      @update="handleUpdateHabit"
    />

    <AddEditCategoryModal
      :visible="showCategoryModal"
      :edit-data="editCategoryTarget"
      @close="closeCategoryModal"
      @create="handleCreateCategory"
      @update="handleUpdateCategory"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useHabitsStore } from '@/stores/habits'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import type { Habit, HabitCreate, HabitUpdate, HabitCategory, HabitCategoryCreate, HabitCategoryUpdate } from '@/api/client'
import AppSubnav from '@/components/AppSubnav.vue'
import { HABITS_SUBNAV } from '@/config/subnavLinks'

const subnavLinks = HABITS_SUBNAV
import AddEditHabitModal from '@/components/habits/AddEditHabitModal.vue'
import AddEditCategoryModal from '@/components/habits/AddEditCategoryModal.vue'

const store = useHabitsStore()
const { show: notify } = useNotifications()

const showHabitModal = ref(false)
const editHabitTarget = ref<{ id: number; name: string; category_id: number } | null>(null)
const showCategoryModal = ref(false)
const editCategoryTarget = ref<{ id: number; name: string } | null>(null)

onMounted(() => {
  store.fetchManageData()
})

function openEditHabit(habit: Habit) {
  editHabitTarget.value = {
    id: habit.id,
    name: habit.name,
    category_id: habit.category_id,
  }
  showHabitModal.value = true
}

function closeHabitModal() {
  showHabitModal.value = false
  editHabitTarget.value = null
}

function openEditCategory(cat: HabitCategory) {
  editCategoryTarget.value = {
    id: cat.id,
    name: cat.name,
  }
  showCategoryModal.value = true
}

function closeCategoryModal() {
  showCategoryModal.value = false
  editCategoryTarget.value = null
}

async function handleCreateHabit(data: HabitCreate) {
  try {
    await store.createHabit(data)
    notify(`${data.name} added`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to add habit: ${detail}`, 'error')
  }
}

async function handleUpdateHabit(id: number, data: HabitUpdate) {
  const name = store.habits.find((h) => h.id === id)?.name ?? 'Habit'
  try {
    await store.updateHabit(id, data)
    notify(`${name} updated`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to update habit: ${detail}`, 'error')
  }
}

async function handleCreateCategory(data: HabitCategoryCreate) {
  try {
    await store.createCategory(data)
    notify(`${data.name} added`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to add category: ${detail}`, 'error')
  }
}

async function handleUpdateCategory(id: number, data: HabitCategoryUpdate) {
  const name = store.categories.find((c) => c.id === id)?.name ?? 'Category'
  try {
    await store.updateCategory(id, data)
    notify(`${name} updated`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to update category: ${detail}`, 'error')
  }
}

async function handleHibernateHabit(id: number) {
  const name = store.habits.find((h) => h.id === id)?.name ?? 'Habit'
  try {
    await store.hibernateHabit(id)
    notify(`${name} hibernated`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to hibernate habit: ${detail}`, 'error')
  }
}

async function handleReviveHabit(id: number) {
  const name = store.habits.find((h) => h.id === id)?.name ?? 'Habit'
  try {
    await store.reviveHabit(id)
    notify(`${name} revived`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to revive habit: ${detail}`, 'error')
  }
}

async function handleDeleteHabit(id: number) {
  const name = store.habits.find((h) => h.id === id)?.name ?? 'Habit'
  try {
    await store.deleteHabit(id)
    notify(`${name} deleted`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to delete habit: ${detail}`, 'error')
  }
}

async function handleHibernateCategory(id: number) {
  const name = store.categories.find((c) => c.id === id)?.name ?? 'Category'
  try {
    await store.hibernateCategory(id)
    notify(`${name} hibernated`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to hibernate category: ${detail}`, 'error')
  }
}

async function handleReviveCategory(id: number) {
  const name = store.categories.find((c) => c.id === id)?.name ?? 'Category'
  try {
    await store.reviveCategory(id)
    notify(`${name} revived`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to revive category: ${detail}`, 'error')
  }
}

async function handleDeleteCategory(id: number) {
  const name = store.categories.find((c) => c.id === id)?.name ?? 'Category'
  try {
    await store.deleteCategory(id)
    notify(`${name} deleted`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to delete category: ${detail}`, 'error')
  }
}
</script>

<style scoped>
.habits-manage__section-title {
  font-size: var(--fs-500);
  color: var(--clr-primary-300);
  margin-bottom: var(--space-xs);
}

.habits-manage__section-title--muted {
  color: var(--clr-gray-400);
}

.habits-manage__row {
  display: flex;
  align-items: center;
  gap: var(--space-s);
  padding: var(--space-xs) var(--space-s);
  border-bottom: 1px solid var(--clr-gray-800);
  transition: background-color 0.15s;
}

.habits-manage__row:hover {
  background-color: var(--clr-gray-900);
}

.habits-manage__row--muted {
  opacity: 0.6;
}

.habits-manage__category-tag {
  font-size: var(--fs-300);
  color: var(--clr-gray-400);
  background-color: var(--clr-gray-800);
  padding: 2px var(--space-xs);
  border-radius: 4px;
}

.habits-manage__actions {
  display: flex;
  gap: var(--space-xs);
  margin-left: auto;
}

.habits-manage__empty {
  color: var(--clr-gray-500);
  font-style: italic;
}
</style>
