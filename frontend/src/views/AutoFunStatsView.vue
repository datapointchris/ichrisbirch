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
            :data="completedByMonthChartData"
            :options="completedByMonthOptions"
          />
        </div>

        <StatsTable
          :headers="['Activity', 'Completed']"
          :empty="recentlyCompleted.length === 0"
        >
          <template #title>Recently Completed</template>
          <template #empty>No completed activities.</template>
          <StatsTableRow
            v-for="item in recentlyCompleted"
            :key="item.name"
          >
            <span class="stats-name">{{ item.name }}</span>
            <span class="stats-meta">{{ formatDate(item.completed_date, 'shortDate') }}</span>
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
import { formatDate } from '@/composables/formatDate'
import { paletteColors, verticalBarOptions, countByMonth } from '@/composables/useStatsCharts'
import type { AutoFun } from '@/api/client'
import type { StatsCard } from '@/components/stats/StatsSummaryCards.vue'
import AppSubnav from '@/components/AppSubnav.vue'
import { AUTOFUN_SUBNAV } from '@/config/subnavLinks'

const subnavLinks = AUTOFUN_SUBNAV
import StatsSummaryCards from '@/components/stats/StatsSummaryCards.vue'
import StatsTable from '@/components/stats/StatsTable.vue'
import StatsTableRow from '@/components/stats/StatsTableRow.vue'

const logger = createLogger('AutoFunStats')
const { show: notify } = useNotifications()

const items = ref<AutoFun[]>([])
const loading = ref(false)
const error = ref<ApiError | null>(null)

const loaded = computed(() => items.value.length > 0)
const completedItems = computed(() => items.value.filter((i) => i.is_completed))
const activeItems = computed(() => items.value.filter((i) => !i.is_completed))

const summaryCards = computed<StatsCard[]>(() => {
  const total = items.value.length
  const completed = completedItems.value.length
  const pct = total > 0 ? Math.round((completed / total) * 100) : 0
  return [
    { label: 'Total', value: total },
    { label: 'Completed', value: completed },
    { label: 'Remaining', value: activeItems.value.length },
    { label: 'Completion %', value: `${pct}%` },
  ]
})

const completedByMonthData = computed(() => countByMonth(completedItems.value, (i) => i.completed_date))

const completedByMonthChartData = computed(() => {
  if (completedByMonthData.value.length === 0) return { labels: [], datasets: [] }
  const rows = completedByMonthData.value
  return {
    labels: rows.map((r) => r.month),
    datasets: [{ label: 'Completed', data: rows.map((r) => r.count), backgroundColor: paletteColors(rows.length) }],
  }
})

const completedByMonthOptions = computed(() => {
  const data = completedByMonthChartData.value.datasets[0]?.data ?? [1]
  return verticalBarOptions('Activities Completed per Month', data)
})

const recentlyCompleted = computed(() =>
  [...completedItems.value]
    .filter((i) => i.completed_date)
    .sort((a, b) => new Date(b.completed_date!).getTime() - new Date(a.completed_date!).getTime())
    .slice(0, 10)
)

onMounted(async () => {
  loading.value = true
  try {
    const response = await api.get<AutoFun[]>('/autofun/')
    items.value = response.data
    logger.info('autofun_stats_loaded', { count: response.data.length })
  } catch (e) {
    const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
    error.value = apiError
    notify('Failed to load autofun stats', 'error')
    logger.error('autofun_stats_load_failed', { detail: apiError.detail })
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
</style>
