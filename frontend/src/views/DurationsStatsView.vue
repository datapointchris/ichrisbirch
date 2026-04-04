<template>
  <div>
    <AppSubnav :links="subnavLinks" />

    <div class="grid grid--one-column">
      <div
        v-if="loading"
        class="stats-empty"
      >
        Loading...
      </div>

      <div
        v-else-if="error"
        class="stats-empty"
      >
        {{ error.userMessage }}
      </div>

      <template v-else-if="loaded">
        <StatsSummaryCards :cards="summaryCards" />

        <div class="stats-chart">
          <Bar
            :data="byLengthChartData"
            :options="byLengthOptions"
          />
        </div>

        <StatsTable
          :headers="['Name', 'Status', 'Days']"
          :empty="durationLengths.length === 0"
        >
          <template #title>All Durations</template>
          <template #empty>No durations found.</template>
          <StatsTableRow
            v-for="d in durationLengths"
            :key="d.name"
          >
            <span class="stats-name">{{ d.name }}</span>
            <span class="stats-meta">{{ d.active ? 'Active' : 'Ended' }}</span>
            <span class="stats-highlight">{{ d.days }}</span>
          </StatsTableRow>
        </StatsTable>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Bar } from 'vue-chartjs'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import { useNotifications } from '@/composables/useNotifications'
import { getThemeColors, horizontalBarOptions, daysBetween, average } from '@/composables/useStatsCharts'
import type { Duration } from '@/api/client'
import type { StatsCard } from '@/components/stats/StatsSummaryCards.vue'
import AppSubnav from '@/components/AppSubnav.vue'
import { DURATIONS_SUBNAV } from '@/config/subnavLinks'
import StatsSummaryCards from '@/components/stats/StatsSummaryCards.vue'

const subnavLinks = DURATIONS_SUBNAV
import StatsTable from '@/components/stats/StatsTable.vue'
import StatsTableRow from '@/components/stats/StatsTableRow.vue'

const logger = createLogger('DurationsStats')
const { show: notify } = useNotifications()

const durations = ref<Duration[]>([])
const loading = ref(false)
const error = ref<ApiError | null>(null)

const loaded = computed(() => durations.value.length > 0)
const today = new Date().toISOString().slice(0, 10)

const durationLengths = computed(() =>
  durations.value
    .map((d) => ({
      name: d.name,
      days: daysBetween(d.start_date, d.end_date ?? today),
      active: !d.end_date,
    }))
    .sort((a, b) => b.days - a.days)
)

const summaryCards = computed<StatsCard[]>(() => {
  const all = durations.value
  const active = all.filter((d) => !d.end_date)
  const ended = all.filter((d) => d.end_date)
  const avgDays = average(ended.map((d) => daysBetween(d.start_date, d.end_date!)))
  return [
    { label: 'Total', value: all.length },
    { label: 'Active', value: active.length },
    { label: 'Ended', value: ended.length },
    { label: 'Avg Length (Days)', value: avgDays },
  ]
})

const byLengthChartData = computed(() => {
  if (durationLengths.value.length === 0) return { labels: [], datasets: [] }
  const rows = durationLengths.value
  return {
    labels: rows.map((d) => d.name),
    datasets: [
      {
        label: 'Duration Length',
        data: rows.map((d) => d.days),
        backgroundColor: rows.map((d) => (d.active ? getThemeColors().primary : getThemeColors().secondary)),
      },
    ],
  }
})

const byLengthOptions = computed(() => horizontalBarOptions('Duration Lengths (Days)'))

onMounted(async () => {
  loading.value = true
  try {
    const response = await api.get<Duration[]>('/durations/')
    durations.value = response.data
    logger.info('duration_stats_loaded', { count: response.data.length })
  } catch (e) {
    const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
    error.value = apiError
    notify('Failed to load duration stats', 'error')
    logger.error('duration_stats_load_failed', { detail: apiError.detail })
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.stats-empty {
  color: var(--clr-gray-500);
  font-style: italic;
}

.stats-chart {
  padding: var(--space-m);
}

.stats-name {
  color: var(--clr-primary-300);
  font-size: var(--fs-400);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stats-meta {
  color: var(--clr-gray-400);
  font-size: var(--fs-300);
  white-space: nowrap;
}

.stats-highlight {
  font-size: var(--fs-500);
  font-weight: 700;
  color: var(--clr-accent);
  text-align: right;
  white-space: nowrap;
}
</style>
