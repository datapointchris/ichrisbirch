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
        v-for="event in upcomingEvents"
        :key="event.id"
        class="widget-list__item"
      >
        <span class="widget-list__name">{{ event.name }}</span>
        <span class="widget-list__meta">
          {{ formatDate(event.date) }}
          <button
            class="widget-action-btn"
            :class="{ 'widget-action-btn--active': event.attending }"
            :title="event.attending ? 'Un-attend' : 'Attend'"
            @click="toggleAttending(event)"
          >
            {{ event.attending ? '✓' : '○' }}
          </button>
        </span>
      </div>
      <div
        v-if="store.events.length === 0"
        class="widget-empty"
      >
        No events
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useEventsStore } from '@/stores/events'
import type { Event } from '@/api/client'

const store = useEventsStore()

const upcomingEvents = computed(() => store.sortedEvents.filter((e) => new Date(e.date) >= new Date()).slice(0, 8))

const dateFormatter = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' })

function formatDate(dateStr: string): string {
  return dateFormatter.format(new Date(dateStr))
}

async function toggleAttending(event: Event) {
  await store.update(event.id, { attending: !event.attending })
}

onMounted(() => {
  if (store.events.length === 0) store.fetchAll()
})
</script>
