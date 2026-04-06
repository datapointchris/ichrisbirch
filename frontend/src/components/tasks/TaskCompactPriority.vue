<template>
  <div :class="['task task--compact-layout priority', stateClass]">
    <h3 class="task--compact-layout__title">{{ task.name }}</h3>
    <span>Priority: {{ task.priority }}</span>
    <span>Category: {{ task.category }}</span>
    <span>
      <ActionButton
        icon="fa-regular fa-circle-check"
        variant="success"
        title="Complete task"
        @click="$emit('complete', task.id)"
      />
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
import { computed } from 'vue'

const props = defineProps<{ task: Task }>()
defineEmits<{ complete: [id: number]; delete: [id: number] }>()
const stateClass = computed(() => taskStateClass(props.task.priority))
</script>
