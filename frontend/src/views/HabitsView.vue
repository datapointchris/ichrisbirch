<template>
  <div>
    <AppSubnav :links="subnavLinks" />

    <div class="grid grid--one-column grid--tight">
      <div class="grid__item habits__date-nav">
        <button
          class="button--hidden habits__day-step"
          title="Previous day"
          data-testid="habits-prev-day"
          @click="store.stepDay(-1)"
        >
          <i class="fa-solid fa-chevron-left"></i>
        </button>

        <h2 class="habits__date">{{ longDate }}</h2>

        <button
          class="button--hidden habits__day-step"
          title="Next day"
          data-testid="habits-next-day"
          :disabled="store.isToday"
          @click="store.stepDay(1)"
        >
          <i class="fa-solid fa-chevron-right"></i>
        </button>

        <DatePicker
          class="habits__date-picker"
          :model-value="store.selectedDate"
          :max="today"
          data-testid="habits-date-picker"
          @update:model-value="handleDatePicked"
        />

        <button
          v-if="!store.isToday"
          class="button button--small"
          data-testid="habits-today"
          @click="store.goToToday()"
        >
          <span class="button__text">Today</span>
        </button>
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
          <p class="habits__empty">{{ todoEmptyText }}</p>
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
          <p class="habits__empty">{{ doneEmptyText }}</p>
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
import { useHabitsStore, todayKey } from '@/stores/habits'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import AppSubnav from '@/components/AppSubnav.vue'
import DatePicker from '@/components/DatePicker.vue'
import { HABITS_SUBNAV } from '@/config/subnavLinks'

const subnavLinks = HABITS_SUBNAV
import type { Habit } from '@/api/client'
import { formatDate } from '@/composables/formatDate'

const store = useHabitsStore()
const { show: notify } = useNotifications()

const today = todayKey()
const longDate = computed(() => formatDate(store.selectedDate, 'weekdayDate'))
const todoEmptyText = computed(() => (store.isToday ? 'All done for today!' : 'All done for that day.'))
const doneEmptyText = computed(() => (store.isToday ? 'Nothing completed yet.' : 'Nothing completed that day.'))

onMounted(() => {
  store.fetchDailyData()
})

function handleDatePicked(day: string) {
  // The picker emits '' on clear, which is not a day to show.
  if (day) store.selectDay(day)
}

async function handleComplete(habit: Habit) {
  try {
    await store.completeHabit(habit)
    const when = store.isToday ? '' : ` for ${formatDate(store.selectedDate, 'shortDate')}`
    notify(`${habit.name} completed${when}`, 'success')
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to complete habit: ${detail}`, 'error')
  }
}
</script>
