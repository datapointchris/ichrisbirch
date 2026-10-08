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
    <span>
      <ActionButton
        data-testid="task-pin-button"
        :icon="task.pinned ? 'fa-solid fa-thumbtack' : 'fa-solid fa-thumbtack-slash'"
        :variant="task.pinned ? 'success' : undefined"
        :title="task.pinned ? 'Pinned — click to unpin' : 'Pin to the top'"
        @click="$emit('pin', task.id, !task.pinned)"
      />
    </span>
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
        data-testid="task-snooze-button"
        class="button"
        title="Not now — move this task back down the list"
        @click="$emit('snooze', task.id)"
      >
        <span class="button__text">Snooze</span>
      </button>
    </span>
    <span>
      <button
        data-testid="task-drop-button"
        class="button"
        title="Let this task go — it stays on record but leaves the list"
        @click="$emit('drop', task.id)"
      >
        <span class="button__text">Drop</span>
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
defineEmits<{
  complete: [id: number]
  snooze: [id: number]
  drop: [id: number]
  pin: [id: number, pinned: boolean]
  delete: [id: number]
}>()
</script>
