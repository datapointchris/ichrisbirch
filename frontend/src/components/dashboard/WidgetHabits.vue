<template>
  <div class="widget-list">
    <div
      v-if="store.loading"
      class="widget-loading"
    >
      Loading...
    </div>
    <template v-else>
      <div
        v-for="habit in todoList"
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
      <div
        v-for="habit in doneList"
        :key="'done-' + habit.id"
        class="widget-list__item widget-list__item--done"
      >
        <span class="widget-list__name">{{ habit.name }}</span>
        <span class="widget-action-btn widget-action-btn--active">✓</span>
      </div>
      <div
        v-if="todoList.length === 0 && doneList.length === 0"
        class="widget-empty"
      >
        No habits
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useHabitsStore } from '@/stores/habits'
import type { Habit } from '@/api/client'

const store = useHabitsStore()

// Flatten grouped records into arrays
const todoList = computed(() => Object.values(store.todoHabits).flat() as Habit[])
const doneList = computed(() => Object.values(store.doneHabits).flat())

async function complete(habit: Habit) {
  await store.completeHabit(habit)
}

onMounted(async () => {
  if (store.habits.length === 0) await store.fetchHabits()
  if (store.completedHabits.length === 0) {
    store.selectedFilter = 'today'
    await store.fetchCompleted()
  }
})
</script>
