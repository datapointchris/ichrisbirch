<template>
  <div>
    <HabitsSubnav active="manage" />

    <div
      v-if="store.loading"
      class="grid grid--one-column"
    >
      <div class="grid__item">Loading...</div>
    </div>

    <template v-else>
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
            class="habits-manage__row"
          >
            <span>{{ habit.name }}</span>
            <span class="habits-manage__category-tag">{{ habit.category.name }}</span>
            <button
              class="button"
              @click="handleHibernateHabit(habit.id)"
            >
              <span class="button__text">Hibernate</span>
            </button>
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
            class="habits-manage__row habits-manage__row--muted"
          >
            <span>{{ habit.name }}</span>
            <span class="habits-manage__category-tag">{{ habit.category.name }}</span>
            <div class="habits-manage__actions">
              <button
                class="button"
                @click="handleReviveHabit(habit.id)"
              >
                <span class="button__text">Revive</span>
              </button>
              <button
                class="button--hidden"
                @click="handleDeleteHabit(habit.id)"
              >
                <i class="button-icon danger fa-regular fa-trash-can"></i>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Add Habit -->
      <div class="add-item-wrapper">
        <h3>Add New Habit</h3>
        <form
          class="add-item-form"
          @submit.prevent="handleAddHabit"
        >
          <div class="add-item-form__item">
            <label for="habit-name">Name:</label>
            <input
              id="habit-name"
              v-model="habitForm.name"
              type="text"
              class="textbox"
              required
            />
          </div>
          <div class="add-item-form__item">
            <label for="habit-category">Category:</label>
            <select
              id="habit-category"
              v-model="habitForm.category_id"
              class="textbox"
              required
            >
              <option
                value=""
                disabled
              >
                Select a category
              </option>
              <option
                v-for="cat in store.currentCategories"
                :key="cat.id"
                :value="cat.id"
              >
                {{ cat.name }}
              </option>
            </select>
          </div>
          <div class="add-item-form__item">
            <button
              type="submit"
              class="button"
            >
              <span class="button__text">Add Habit</span>
            </button>
          </div>
        </form>
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
            class="habits-manage__row"
          >
            <span>{{ cat.name }}</span>
            <button
              class="button"
              @click="handleHibernateCategory(cat.id)"
            >
              <span class="button__text">Hibernate</span>
            </button>
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
            class="habits-manage__row habits-manage__row--muted"
          >
            <span>{{ cat.name }}</span>
            <div class="habits-manage__actions">
              <button
                class="button"
                @click="handleReviveCategory(cat.id)"
              >
                <span class="button__text">Revive</span>
              </button>
              <button
                class="button--hidden"
                @click="handleDeleteCategory(cat.id)"
              >
                <i class="button-icon danger fa-regular fa-trash-can"></i>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Add Category -->
      <div class="add-item-wrapper">
        <h3>Add New Category</h3>
        <form
          class="add-item-form"
          @submit.prevent="handleAddCategory"
        >
          <div class="add-item-form__item">
            <label for="category-name">Name:</label>
            <input
              id="category-name"
              v-model="categoryForm.name"
              type="text"
              class="textbox"
              required
            />
          </div>
          <div class="add-item-form__item">
            <button
              type="submit"
              class="button"
            >
              <span class="button__text">Add Category</span>
            </button>
          </div>
        </form>
      </div>

      <!-- Completed Habits -->
      <div
        v-if="store.completedHabits.length > 0"
        class="grid grid--one-column grid--tight"
      >
        <div class="grid__item">
          <h3 class="habits-manage__section-title">Completed Habits</h3>
          <div
            v-for="completed in store.completedHabits"
            :key="completed.id"
            class="habits-manage__row"
          >
            <span>{{ completed.name }}</span>
            <span class="habits-manage__category-tag">{{ completed.category.name }}</span>
            <span class="habits-manage__date">{{ formatDate(completed.complete_date) }}</span>
            <button
              class="button--hidden"
              @click="handleDeleteCompleted(completed.id)"
            >
              <i class="button-icon danger fa-regular fa-trash-can"></i>
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import { useHabitsStore } from '@/stores/habits'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import HabitsSubnav from '@/components/HabitsSubnav.vue'

const store = useHabitsStore()
const { show: notify } = useNotifications()

const habitForm = reactive({ name: '', category_id: '' as string | number })
const categoryForm = reactive({ name: '' })

onMounted(() => {
  store.fetchManageData()
})

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

async function handleAddHabit() {
  if (!habitForm.name.trim() || !habitForm.category_id) return
  try {
    await store.createHabit({ name: habitForm.name.trim(), category_id: Number(habitForm.category_id) })
    notify('Habit added', 'success')
    habitForm.name = ''
    habitForm.category_id = ''
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to add habit: ${detail}`, 'error')
  }
}

async function handleAddCategory() {
  if (!categoryForm.name.trim()) return
  try {
    await store.createCategory({ name: categoryForm.name.trim() })
    notify('Category added', 'success')
    categoryForm.name = ''
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to add category: ${detail}`, 'error')
  }
}

async function handleHibernateHabit(id: number) {
  try {
    await store.hibernateHabit(id)
    notify('Habit hibernated', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to hibernate habit: ${detail}`, 'error')
  }
}

async function handleReviveHabit(id: number) {
  try {
    await store.reviveHabit(id)
    notify('Habit revived', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to revive habit: ${detail}`, 'error')
  }
}

async function handleDeleteHabit(id: number) {
  try {
    await store.deleteHabit(id)
    notify('Habit deleted', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to delete habit: ${detail}`, 'error')
  }
}

async function handleHibernateCategory(id: number) {
  try {
    await store.hibernateCategory(id)
    notify('Category hibernated', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to hibernate category: ${detail}`, 'error')
  }
}

async function handleReviveCategory(id: number) {
  try {
    await store.reviveCategory(id)
    notify('Category revived', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to revive category: ${detail}`, 'error')
  }
}

async function handleDeleteCategory(id: number) {
  try {
    await store.deleteCategory(id)
    notify('Category deleted', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to delete category: ${detail}`, 'error')
  }
}

async function handleDeleteCompleted(id: number) {
  try {
    await store.deleteCompleted(id)
    notify('Completed habit entry deleted', 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to delete: ${detail}`, 'error')
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

.habits-manage__date {
  font-size: var(--fs-300);
  color: var(--clr-gray-500);
  margin-left: auto;
}

.habits-manage__actions {
  display: flex;
  gap: var(--space-xs);
  margin-left: auto;
}

.habits-manage__empty {
  color: var(--clr-gray-500);
  font-style: italic;
  padding: var(--space-xs) 0;
}
</style>
