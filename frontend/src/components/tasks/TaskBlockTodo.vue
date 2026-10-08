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
    <div class="task--block-layout__pin">
      <ActionButton
        data-testid="task-pin-button"
        :icon="task.pinned ? 'fa-solid fa-thumbtack' : 'fa-solid fa-thumbtack-slash'"
        :variant="task.pinned ? 'success' : undefined"
        :title="task.pinned ? 'Pinned — click to unpin' : 'Pin to the top'"
        @click="$emit('pin', task.id, !task.pinned)"
      />
      <span v-if="task.pinned"> Pinned</span>
    </div>
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
        data-testid="task-snooze-button"
        class="button"
        title="Not now — move this task back down the list"
        @click="$emit('snooze', task.id)"
      >
        <span class="button__text">Snooze</span>
      </button>
      <button
        data-testid="task-drop-button"
        class="button"
        title="Let this task go — it stays on record but leaves the list"
        @click="$emit('drop', task.id)"
      >
        <span class="button__text">Drop</span>
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
