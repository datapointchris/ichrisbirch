<template>
  <div
    class="task task--compact-layout dropped task--dropped"
    data-testid="task-dropped-item"
  >
    <h3 class="task--compact-layout__title">{{ task.name }}</h3>
    <span>{{ task.category }}</span>
    <span>Added {{ formatDate(task.add_date, 'shortDate') }}</span>
    <span>Dropped {{ formatDate(task.drop_date, 'shortDate') }}</span>
    <span>{{ task.drop_reason || 'No reason given' }}</span>
    <span>
      <button
        class="button"
        data-testid="task-reopen-button"
        @click="$emit('reopen', task.id)"
      >
        <span class="button__text">Reopen</span>
      </button>
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
import type { DroppedTask } from '@/stores/tasks'
import ActionButton from '@/components/ActionButton.vue'
import { formatDate } from '@/composables/formatDate'

defineProps<{ task: DroppedTask }>()
defineEmits<{ reopen: [id: number]; delete: [id: number] }>()
</script>
