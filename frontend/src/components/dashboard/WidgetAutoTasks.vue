<template>
  <div class="widget-list">
    <div
      v-if="store.loading"
      class="widget-loading"
    >
      Loading...
    </div>
    <template v-else>
      <div
        v-for="task in recentAutoTasks"
        :key="task.id"
        class="widget-list__item"
      >
        <span class="widget-list__name">{{ task.name }}</span>
        <span class="widget-list__meta">
          <span class="widget-list__tag">{{ task.frequency }}</span>
          <span>×{{ task.run_count }}</span>
        </span>
      </div>
      <div
        v-if="store.autotasks.length === 0"
        class="widget-empty"
      >
        No autotasks
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useAutoTasksStore } from '@/stores/autotasks'

const store = useAutoTasksStore()

const recentAutoTasks = computed(() => store.sortedAutoTasks.slice(0, 8))

onMounted(() => {
  if (store.autotasks.length === 0) store.fetchAll()
})
</script>
