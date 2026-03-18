<template>
  <div :class="['task task--compact-layout todo', stateClass]">
    <h3 class="task--compact-layout__title">{{ task.name }}</h3>
    <span>Priority: {{ task.priority }}</span>
    <span>Category: {{ task.category }}</span>
    <span>Add Date: {{ prettyDate(task.add_date) }}</span>
    <span>
      <button
        class="button"
        @click="$emit('complete', task.id)"
      >
        <span class="button__text">Complete Task</span>
      </button>
    </span>
    <span>
      <button
        class="button"
        @click="$emit('extend', task.id, 7)"
      >
        <span class="button__text">Extend 7 Days</span>
      </button>
    </span>
    <span>
      <button
        class="button"
        @click="$emit('extend', task.id, 30)"
      >
        <span class="button__text">Extend 30 Days</span>
      </button>
    </span>
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
import type { Task } from '@/api/client'
import { taskStateClass, prettyDate } from './taskUtils'
import { computed } from 'vue'

const props = defineProps<{ task: Task }>()
defineEmits<{ complete: [id: number]; extend: [id: number, days: number]; delete: [id: number] }>()
const stateClass = computed(() => taskStateClass(props.task.priority))
</script>
