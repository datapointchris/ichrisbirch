<template>
  <div class="task task--compact-layout completed task--complete">
    <h3 class="task--compact-layout__title">{{ task.name }}</h3>
    <span>Category: {{ task.category }}</span>
    <span>Age: {{ timeToComplete(task) }}</span>
    <span>
      <ActionButton
        data-testid="task-edit-button"
        icon="fa-solid fa-pen-to-square"
        variant="warning"
        title="Edit task"
        @click="$emit('edit', task.id)"
      />
    </span>
    <span>
      <ActionButton
        icon="fa-regular fa-trash-can"
        variant="danger"
        title="Delete task"
        @click="$emit('delete', task.id)"
      />
    </span>
  </div>
</template>

<script setup lang="ts">
import type { CompletedTask } from '@/stores/tasks'
import ActionButton from '@/components/ActionButton.vue'
import { timeToComplete } from './taskUtils'

defineProps<{ task: CompletedTask }>()
defineEmits<{ edit: [id: number]; delete: [id: number] }>()
</script>
