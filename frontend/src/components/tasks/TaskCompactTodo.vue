<template>
  <div
    data-testid="task-item"
    class="task task--compact-layout todo"
  >
    <span
      class="task-drag-handle"
      title="Drag to reorder"
    >
      <i class="fa-solid fa-grip-lines"></i>
    </span>
    <h3 class="task--compact-layout__title">{{ task.name }}</h3>
    <span>Priority: {{ task.priority }}</span>
    <span>Category: {{ task.category }}</span>
    <span>Add Date: {{ formatDate(task.add_date, 'shortDate') }}</span>
    <span>
      <button
        data-testid="task-complete-button"
        class="button"
        @click="$emit('complete', task.id)"
      >
        <span class="button__text">Complete Task</span>
      </button>
    </span>
    <span>
      <button
        data-testid="task-shift-button"
        class="button"
        title="Shift this task 10 positions down the list"
        @click="$emit('shift', task.id, 10)"
      >
        <span class="button__text">↓ 10</span>
      </button>
    </span>
    <span>
      <ActionButton
        icon="fa-solid fa-pen-to-square"
        variant="warning"
        title="Edit task"
      />
    </span>
    <span>
      <ActionButton
        data-testid="task-delete-button"
        icon="fa-regular fa-trash-can"
        variant="danger"
        title="Delete task"
        @click="$emit('delete', task.id)"
      />
    </span>
  </div>
</template>

<script setup lang="ts">
import type { Task } from '@/api/client'
import ActionButton from '@/components/ActionButton.vue'
import { formatDate } from '@/composables/formatDate'

defineProps<{ task: Task }>()
defineEmits<{ complete: [id: number]; shift: [id: number, positions: number]; delete: [id: number] }>()
</script>
