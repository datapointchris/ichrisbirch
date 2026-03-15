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
        v-for="duration in activeDurations"
        :key="duration.id"
        class="widget-list__item"
      >
        <span class="widget-list__name">{{ duration.name }}</span>
        <span class="widget-list__meta">{{ elapsed(duration.start_date) }}</span>
      </div>
      <div
        v-if="activeDurations.length === 0"
        class="widget-empty"
      >
        No active durations
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useDurationsStore } from '@/stores/durations'

const store = useDurationsStore()

const activeDurations = computed(() => store.sortedDurations.filter((d) => !d.end_date).slice(0, 8))

function elapsed(startDate: string): string {
  const days = Math.floor((Date.now() - new Date(startDate).getTime()) / 86_400_000)
  if (days < 1) return 'Today'
  if (days < 30) return `${days}d`
  if (days < 365) return `${Math.floor(days / 30)}mo`
  return `${(days / 365).toFixed(1)}y`
}

onMounted(() => {
  if (store.durations.length === 0) store.fetchAll()
})
</script>
