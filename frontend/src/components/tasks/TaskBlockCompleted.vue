<template>
  <div class="task task--block-layout completed task--complete">
    <h3 class="task--block-layout__title">{{ task.name }}</h3>
    <div class="task--block-layout__category">Category: {{ task.category }}</div>
    <div class="task--block-layout__add-date">Add Date: {{ prettyDate(task.add_date) }}</div>
    <div class="task--block-layout__complete-date">Complete Date: {{ prettyDate(task.complete_date) }}</div>
    <div class="task--block-layout__time-to-complete">Time to Complete: {{ timeToComplete(task) }}</div>
    <div
      v-if="task.notes"
      class="task--block-layout__notes"
    >
      <strong>Notes: </strong>{{ task.notes }}
    </div>
    <div class="task--block-layout__buttons">
      <button
        class="button button--danger"
        @click="$emit('delete', task.id)"
      >
        <span class="button__text button__text--danger">Delete Task</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { CompletedTask } from '@/stores/tasks'
import { timeToComplete, prettyDate } from './taskUtils'

defineProps<{ task: CompletedTask }>()
defineEmits<{ delete: [id: number] }>()
</script>
