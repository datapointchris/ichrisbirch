<template>
  <div
    class="task task--block-layout dropped task--dropped"
    data-testid="task-dropped-item"
  >
    <h3 class="task--block-layout__title">{{ task.name }}</h3>
    <div class="task--block-layout__category">Category: {{ task.category }}</div>
    <div class="task--block-layout__add-date">Add Date: {{ formatDate(task.add_date, 'shortDate') }}</div>
    <div class="task--block-layout__drop-date">Drop Date: {{ formatDate(task.drop_date, 'shortDate') }}</div>
    <div class="task--block-layout__drop-reason">{{ task.drop_reason ? `Reason: ${task.drop_reason}` : 'No reason given' }}</div>
    <div
      v-if="task.notes"
      class="task--block-layout__notes"
    >
      <strong>Notes: </strong>{{ task.notes }}
    </div>
    <div class="task--block-layout__buttons">
      <button
        class="button"
        data-testid="task-reopen-button"
        @click="$emit('reopen', task.id)"
      >
        <span class="button__text">Reopen</span>
      </button>
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
import type { DroppedTask } from '@/stores/tasks'
import { formatDate } from '@/composables/formatDate'

defineProps<{ task: DroppedTask }>()
defineEmits<{ reopen: [id: number]; delete: [id: number] }>()
</script>
