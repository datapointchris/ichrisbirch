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
        v-for="countdown in topCountdowns"
        :key="countdown.id"
        class="widget-list__item"
      >
        <span class="widget-list__name">{{ countdown.name }}</span>
        <span class="widget-list__meta">{{ daysLeft(countdown.due_date) }}</span>
      </div>
      <div
        v-if="store.countdowns.length === 0"
        class="widget-empty"
      >
        No countdowns
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useCountdownsStore } from '@/stores/countdowns'

const store = useCountdownsStore()

const topCountdowns = computed(() => store.sortedCountdowns.slice(0, 8))

function daysLeft(dateStr: string): string {
  const diff = Math.ceil((new Date(dateStr).getTime() - Date.now()) / 86_400_000)
  if (diff < 0) return 'Past'
  if (diff === 0) return 'Today'
  if (diff === 1) return '1 day'
  return `${diff} days`
}

onMounted(() => {
  if (store.countdowns.length === 0) store.fetchAll()
})
</script>
