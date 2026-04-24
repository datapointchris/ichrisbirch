<template>
  <div
    data-testid="task-item"
    class="task task--block-layout todo"
  >
    <span
      class="task-drag-handle"
      title="Drag to reorder"
    >
      <i class="fa-solid fa-grip-lines"></i>
    </span>
    <h3 class="task--block-layout__title">{{ task.name }}</h3>
    <div class="task--block-layout__priority">Priority: {{ task.priority }}</div>
    <div class="task--block-layout__category">Category: {{ task.category }}</div>
    <div class="task--block-layout__add-date">Add Date: {{ formatDate(task.add_date, 'shortDate') }}</div>
    <div
      v-if="task.notes"
      class="task--block-layout__notes"
    >
      <strong>Notes: </strong>{{ task.notes }}
    </div>
    <div class="task--block-layout__buttons">
      <button
        data-testid="task-complete-button"
        class="button"
        @click="$emit('complete', task.id)"
      >
        <span class="button__text">Complete Task</span>
      </button>
      <button
        data-testid="task-shift-button"
        class="button"
        title="Shift this task 10 positions down the list"
        @click="$emit('shift', task.id, 10)"
      >
        <span class="button__text">↓ 10</span>
      </button>
      <button
        data-testid="task-delete-button"
        class="button button--danger"
        @click="$emit('delete', task.id)"
      >
        <span class="button__text button__text--danger">Delete Task</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Task } from '@/api/client'
import { formatDate } from '@/composables/formatDate'

defineProps<{ task: Task }>()
defineEmits<{ complete: [id: number]; shift: [id: number, positions: number]; delete: [id: number] }>()
</script>
