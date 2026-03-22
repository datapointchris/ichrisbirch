<template>
  <div
    data-testid="task-item"
    :class="['task task--block-layout todo', stateClass]"
  >
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
        data-testid="task-extend-7-button"
        class="button"
        @click="$emit('extend', task.id, 7)"
      >
        <span class="button__text">Extend 7 Days</span>
      </button>
      <button
        data-testid="task-extend-30-button"
        class="button"
        @click="$emit('extend', task.id, 30)"
      >
        <span class="button__text">Extend 30 Days</span>
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
import { taskStateClass } from './taskUtils'
import { formatDate } from '@/composables/formatDate'
import { computed } from 'vue'

const props = defineProps<{ task: Task }>()
defineEmits<{ complete: [id: number]; extend: [id: number, days: number]; delete: [id: number] }>()
const stateClass = computed(() => taskStateClass(props.task.priority))
</script>
