<template>
  <div class="widget-list">
    <div
      v-if="loading"
      class="widget-loading"
    >
      Loading...
    </div>
    <template v-else>
      <div
        v-for="task in topTasks"
        :key="task.id"
        class="widget-list__item"
      >
        <span class="widget-list__name">{{ task.name }}</span>
        <span class="widget-list__meta">
          <span class="widget-list__tag">{{ task.category }}</span>
          <button
            class="widget-action-btn"
            title="Complete"
            @click="completeTask(task.id)"
          >
            ○
          </button>
        </span>
      </div>
      <div
        v-if="tasks.length === 0"
        class="widget-empty"
      >
        No tasks
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api } from '@/api/client'
import type { Task } from '@/api/client'
import { createLogger } from '@/utils/logger'

const logger = createLogger('WidgetTasks')

// Tasks doesn't have a Pinia store yet — call API directly
const tasks = ref<Task[]>([])
const loading = ref(false)

const topTasks = computed(() => [...tasks.value].sort((a, b) => a.priority - b.priority).slice(0, 10))

async function fetchTasks() {
  loading.value = true
  try {
    const response = await api.get<Task[]>('/tasks/todo/')
    tasks.value = response.data
    logger.info('tasks_fetched', { count: response.data.length })
  } catch (e) {
    logger.error('tasks_fetch_failed', { error: String(e) })
  } finally {
    loading.value = false
  }
}

async function completeTask(id: number) {
  try {
    await api.patch(`/tasks/${id}/complete/`)
    tasks.value = tasks.value.filter((t) => t.id !== id)
    logger.info('task_completed', { id })
  } catch (e) {
    logger.error('task_complete_failed', { id, error: String(e) })
  }
}

onMounted(() => fetchTasks())

defineExpose({ fetchTasks })
</script>
