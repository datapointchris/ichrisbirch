<template>
  <div :class="['task task--compact-layout priority', stateClass]">
    <h3 class="task--compact-layout__title">{{ task.name }}</h3>
    <span>Priority: {{ task.priority }}</span>
    <span>Category: {{ task.category }}</span>
    <span>
      <button
        class="button--hidden"
        @click="$emit('complete', task.id)"
      >
        <i class="button-icon success fa-regular fa-circle-check"></i>
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
import { taskStateClass } from './taskUtils'
import { computed } from 'vue'

const props = defineProps<{ task: Task }>()
defineEmits<{ complete: [id: number]; delete: [id: number] }>()
const stateClass = computed(() => taskStateClass(props.task.priority))
</script>
