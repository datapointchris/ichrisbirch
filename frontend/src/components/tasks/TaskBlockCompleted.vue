<template>
  <div class="task task--block-layout completed task--complete">
    <h3 class="task--block-layout__title">{{ task.name }}</h3>
    <div class="task--block-layout__category">Category: {{ task.category }}</div>
    <div class="task--block-layout__add-date">Add Date: {{ formatDate(task.add_date, 'shortDate') }}</div>
    <div class="task--block-layout__complete-date">Complete Date: {{ formatDate(task.complete_date, 'shortDate') }}</div>
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
import { timeToComplete } from './taskUtils'
import { formatDate } from '@/composables/formatDate'

defineProps<{ task: CompletedTask }>()
defineEmits<{ delete: [id: number] }>()
</script>
