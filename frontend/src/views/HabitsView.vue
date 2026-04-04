<template>
  <div>
    <AppSubnav :links="subnavLinks" />

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
import AppSubnav from '@/components/AppSubnav.vue'
import { HABITS_SUBNAV } from '@/config/subnavLinks'

const subnavLinks = HABITS_SUBNAV
import type { Habit } from '@/api/client'
import { formatDate } from '@/composables/formatDate'

const store = useHabitsStore()
const { show: notify } = useNotifications()

const longDate = computed(() => formatDate(new Date().toISOString(), 'weekdayDate'))

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
