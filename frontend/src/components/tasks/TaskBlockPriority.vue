<template>
  <div class="task task--block-layout priority">
    <h3 class="task--block-layout__title">{{ task.name }}</h3>
    <div class="task--block-layout__priority">Priority: {{ task.priority }}</div>
    <div class="task--block-layout__category">Category: {{ task.category }}</div>
    <div class="task--block-layout__add-date">Add Date: {{ formatDate(task.add_date, 'shortDate') }}</div>
    <div
      v-if="task.notes"
      class="task--block-layout__notes"
    >
      <strong>Notes:</strong>{{ task.notes }}
    </div>
    <div class="task--block-layout__buttons">
      <button
        class="button"
        @click="$emit('complete', task.id)"
      >
        <span class="button__text">Complete Task</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Task } from '@/api/client'
import { formatDate } from '@/composables/formatDate'

defineProps<{ task: Task }>()
defineEmits<{ complete: [id: number] }>()
</script>
