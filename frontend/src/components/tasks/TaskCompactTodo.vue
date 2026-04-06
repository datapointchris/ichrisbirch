<template>
  <div
    data-testid="task-item"
    :class="['task task--compact-layout todo', stateClass]"
  >
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
        data-testid="task-extend-7-button"
        class="button"
        @click="$emit('extend', task.id, 7)"
      >
        <span class="button__text">Extend 7 Days</span>
      </button>
    </span>
    <span>
      <button
        data-testid="task-extend-30-button"
        class="button"
        @click="$emit('extend', task.id, 30)"
      >
        <span class="button__text">Extend 30 Days</span>
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
import { taskStateClass } from './taskUtils'
import { formatDate } from '@/composables/formatDate'
import { computed } from 'vue'

const props = defineProps<{ task: Task }>()
defineEmits<{ complete: [id: number]; extend: [id: number, days: number]; delete: [id: number] }>()
const stateClass = computed(() => taskStateClass(props.task.priority))
</script>
