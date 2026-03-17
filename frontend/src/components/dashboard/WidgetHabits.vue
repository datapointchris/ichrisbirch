<template>
  <div class="widget-list">
    <div
      v-if="store.loading"
      class="widget-loading"
    >
      Loading...
    </div>
    <template v-else>
      <template
        v-for="(habits, category) in store.todoHabits"
        :key="'todo-' + category"
      >
        <div class="widget-list__category">{{ category }}</div>
        <div
          v-for="habit in habits"
          :key="habit.id"
          class="widget-list__item"
        >
          <span class="widget-list__name">{{ habit.name }}</span>
          <button
            class="widget-action-btn"
            title="Complete"
            @click="complete(habit)"
          >
            ○
          </button>
        </div>
      </template>
      <template
        v-for="(habits, category) in store.doneHabits"
        :key="'done-' + category"
      >
        <div class="widget-list__category">{{ category }}</div>
        <div
          v-for="habit in habits"
          :key="habit.id"
          class="widget-list__item widget-list__item--done"
        >
          <span class="widget-list__name">{{ habit.name }}</span>
          <span class="widget-action-btn widget-action-btn--active">✓</span>
        </div>
      </template>
      <div
        v-if="todoCount === 0 && doneCount === 0"
        class="widget-empty"
      >
        No habits tracked
      </div>
      <div
        v-else-if="todoCount === 0"
        class="widget-empty"
      >
        All done for today!
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useHabitsStore } from '@/stores/habits'
import type { Habit } from '@/api/client'

const store = useHabitsStore()

const todoCount = computed(() => Object.values(store.todoHabits).flat().length)
const doneCount = computed(() => Object.values(store.doneHabits).flat().length)

async function complete(habit: Habit) {
  await store.completeHabit(habit)
}

onMounted(async () => {
  await store.fetchDailyData()
})
</script>
