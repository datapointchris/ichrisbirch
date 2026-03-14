<template>
  <div>
    <HabitsSubnav active="daily" />

    <div class="grid grid--one-column grid--tight">
      <div class="grid__item">
        <h2 class="habits__date">{{ longDate }}</h2>
      </div>
    </div>

    <div
      v-if="store.loading"
      class="grid grid--one-column"
    >
      <div class="grid__item">Loading...</div>
    </div>

    <div
      v-else
      class="habits__daily"
    >
      <!-- To Do -->
      <div class="habits__column">
        <h3 class="habits__column-title">To Do</h3>
        <template v-if="Object.keys(store.todoHabits).length === 0">
          <p class="habits__empty">All done for today!</p>
        </template>
        <template
          v-for="(habits, category) in store.todoHabits"
          :key="category"
        >
          <div class="habits__category">
            <h4 class="habits__category-name">{{ category }}</h4>
            <div
              v-for="habit in habits"
              :key="habit.id"
              class="habits__item"
            >
              <span class="habits__item-name">{{ habit.name }}</span>
              <button
                class="button--hidden habits__check"
                title="Complete"
                @click="handleComplete(habit)"
              >
                <i class="fa-solid fa-check"></i>
              </button>
            </div>
          </div>
        </template>
      </div>

      <!-- Done -->
      <div class="habits__column">
        <h3 class="habits__column-title habits__column-title--done">Done</h3>
        <template v-if="Object.keys(store.doneHabits).length === 0">
          <p class="habits__empty">Nothing completed yet.</p>
        </template>
        <template
          v-for="(habits, category) in store.doneHabits"
          :key="category"
        >
          <div class="habits__category">
            <h4 class="habits__category-name">{{ category }}</h4>
            <div
              v-for="habit in habits"
              :key="habit.id"
              class="habits__item habits__item--done"
            >
              <span class="habits__item-name">{{ habit.name }}</span>
              <i class="fa-solid fa-circle-check habits__done-icon"></i>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useHabitsStore } from '@/stores/habits'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import HabitsSubnav from '@/components/HabitsSubnav.vue'
import type { Habit } from '@/api/client'

const store = useHabitsStore()
const { show: notify } = useNotifications()

const longDate = computed(() => {
  return new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
})

onMounted(() => {
  store.fetchDailyData()
})

async function handleComplete(habit: Habit) {
  try {
    await store.completeHabit(habit)
    notify(`${habit.name} completed`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to complete habit: ${detail}`, 'error')
  }
}
</script>

<style scoped>
.habits__date {
  color: var(--clr-gray-300);
  font-size: var(--fs-500);
  font-weight: 400;
}

.habits__daily {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-l);
  padding: var(--space-s) 0;
}

.habits__column-title {
  font-size: var(--fs-500);
  color: var(--clr-primary-300);
  margin-bottom: var(--space-s);
  padding-bottom: var(--space-3xs);
  border-bottom: 2px solid var(--clr-primary-400);
}

.habits__column-title--done {
  color: var(--clr-green-400, #4ade80);
  border-bottom-color: var(--clr-green-400, #4ade80);
}

.habits__category {
  margin-bottom: var(--space-m);
}

.habits__category-name {
  font-size: var(--fs-300);
  color: var(--clr-gray-400);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-xs);
}

.habits__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-xs) var(--space-s);
  border-bottom: 1px solid var(--clr-gray-800);
  transition: background-color 0.15s;
}

.habits__item:hover {
  background-color: var(--clr-gray-900);
}

.habits__item--done {
  opacity: 0.7;
}

.habits__item-name {
  font-size: var(--fs-400);
}

.habits__check {
  color: var(--clr-primary-400);
  font-size: var(--fs-500);
  cursor: pointer;
  transition:
    color 0.15s,
    transform 0.15s;
}

.habits__check:hover {
  color: var(--clr-green-400, #4ade80);
  transform: scale(1.2);
}

.habits__done-icon {
  color: var(--clr-green-400, #4ade80);
  font-size: var(--fs-400);
}

.habits__empty {
  color: var(--clr-gray-500);
  font-style: italic;
  padding: var(--space-s);
}

@media (max-width: 768px) {
  .habits__daily {
    grid-template-columns: 1fr;
  }
}
</style>
