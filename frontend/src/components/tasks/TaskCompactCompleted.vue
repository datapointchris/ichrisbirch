<template>
  <div class="task task--compact-layout completed task--complete">
    <h3 class="task--compact-layout__title">{{ task.name }}</h3>
    <span>Category: {{ task.category }}</span>
    <span>Age: {{ timeToComplete(task) }}</span>
    <span>
      <i class="button-icon warning fa-solid fa-pen-to-square"></i>
    </span>
    <span>
      <button
        class="button--hidden"
        @click="$emit('delete', task.id)"
      >
        <i class="button-icon danger fa-regular fa-trash-can"></i>
      </button>
    </span>
  </div>
</template>

<script setup lang="ts">
import type { CompletedTask } from '@/stores/tasks'
import { timeToComplete } from './taskUtils'

defineProps<{ task: CompletedTask }>()
defineEmits<{ delete: [id: number] }>()
</script>
