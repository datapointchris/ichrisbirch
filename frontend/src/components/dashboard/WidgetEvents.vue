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
          {{ formatDate(event.date, 'monthDay') }}
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
        v-if="upcomingEvents.length === 0"
        class="widget-empty"
      >
        No upcoming events
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useEventsStore } from '@/stores/events'
import type { Event } from '@/api/client'
import { formatDate } from '@/composables/formatDate'
import { compareWallClocks, wallClockInstant } from '@/composables/useWallClock'
import { dayKeyOf, todayKey } from '@/composables/calendarDay'

const store = useEventsStore()

// Upcoming is today onward, as the API reads `when=upcoming`, so an event this
// morning stays listed all day. e.date is the venue's clock, so it is resolved
// before its day is read.
const upcomingEvents = computed(() => {
  const today = todayKey()
  return store.events
    .filter((e) => dayKeyOf(wallClockInstant(e)) >= today)
    .sort(compareWallClocks)
    .slice(0, 8)
})

async function toggleAttending(event: Event) {
  await store.update(event.id, { attending: !event.attending })
}

onMounted(() => {
  if (store.events.length === 0) store.fetchAll()
})
</script>
