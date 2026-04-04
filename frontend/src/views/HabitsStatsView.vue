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
            :data="byCategoryChartData"
            :options="byCategoryOptions"
          />
        </div>

        <div class="stats-chart">
          <Bar
            :data="completedByMonthChartData"
            :options="completedByMonthOptions"
          />
        </div>

        <div class="stats-chart">
          <Bar
            :data="topHabitsChartData"
            :options="topHabitsOptions"
          />
        </div>

        <StatsTable
          :headers="['Habit', 'Category', 'Completions']"
          :empty="topHabits.length === 0"
        >
          <template #title>Top Habits</template>
          <template #empty>No habit completions yet.</template>
          <StatsTableRow
            v-for="habit in topHabits"
            :key="habit.name"
          >
            <span class="stats-name">{{ habit.name }}</span>
            <span class="stats-meta">{{ habit.categoryName }}</span>
            <span class="stats-highlight">{{ habit.count }}</span>
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
import { paletteColors, horizontalBarOptions, verticalBarOptions, countByMonth, countByLabel } from '@/composables/useStatsCharts'
import type { HabitCompleted, HabitCategory } from '@/api/client'
import type { StatsCard } from '@/components/stats/StatsSummaryCards.vue'
import AppSubnav from '@/components/AppSubnav.vue'
import { HABITS_SUBNAV } from '@/config/subnavLinks'

const subnavLinks = HABITS_SUBNAV
import StatsSummaryCards from '@/components/stats/StatsSummaryCards.vue'
import StatsTable from '@/components/stats/StatsTable.vue'
import StatsTableRow from '@/components/stats/StatsTableRow.vue'

const logger = createLogger('HabitsStats')
const { show: notify } = useNotifications()

const completedHabits = ref<HabitCompleted[]>([])
const categories = ref<HabitCategory[]>([])
const loading = ref(false)
const error = ref<ApiError | null>(null)

const loaded = computed(() => completedHabits.value.length > 0)

const summaryCards = computed<StatsCard[]>(() => {
  const completed = completedHabits.value
  return [
    { label: 'Total Completions', value: completed.length },
    { label: 'Unique Habits', value: new Set(completed.map((h) => h.name)).size },
    { label: 'Active Categories', value: categories.value.filter((c) => c.is_current).length },
  ]
})

const byCategoryData = computed(() => countByLabel(completedHabits.value, (h) => h.category.name))

const byCategoryChartData = computed(() => {
  if (byCategoryData.value.length === 0) return { labels: [], datasets: [] }
  const rows = byCategoryData.value
  return {
    labels: rows.map((r) => r.label),
    datasets: [{ label: 'Completions', data: rows.map((r) => r.count), backgroundColor: paletteColors(rows.length) }],
  }
})

const byCategoryOptions = computed(() => horizontalBarOptions('Completions by Category'))

const completedByMonthData = computed(() => countByMonth(completedHabits.value, (h) => h.complete_date))

const completedByMonthChartData = computed(() => {
  if (completedByMonthData.value.length === 0) return { labels: [], datasets: [] }
  const rows = completedByMonthData.value
  return {
    labels: rows.map((r) => r.month),
    datasets: [{ label: 'Completions', data: rows.map((r) => r.count), backgroundColor: paletteColors(rows.length) }],
  }
})

const completedByMonthOptions = computed(() => {
  const data = completedByMonthChartData.value.datasets[0]?.data ?? [1]
  return verticalBarOptions('Completions per Month', data)
})

const topHabits = computed(() => {
  const grouped = new Map<string, { categoryName: string; count: number }>()
  for (const h of completedHabits.value) {
    const entry = grouped.get(h.name)
    if (entry) entry.count++
    else grouped.set(h.name, { categoryName: h.category.name, count: 1 })
  }
  return [...grouped.entries()]
    .sort(([, a], [, b]) => b.count - a.count)
    .slice(0, 20)
    .map(([name, d]) => ({ name, categoryName: d.categoryName, count: d.count }))
})

const topHabitsChartData = computed(() => {
  if (topHabits.value.length === 0) return { labels: [], datasets: [] }
  const rows = topHabits.value
  return {
    labels: rows.map((r) => r.name),
    datasets: [{ label: 'Completions', data: rows.map((r) => r.count), backgroundColor: paletteColors(rows.length) }],
  }
})

const topHabitsOptions = computed(() => horizontalBarOptions('Top 20 Most Completed Habits'))

onMounted(async () => {
  loading.value = true
  try {
    const [completedRes, categoriesRes] = await Promise.all([
      api.get<HabitCompleted[]>('/habits/completed/'),
      api.get<HabitCategory[]>('/habits/categories/'),
    ])
    completedHabits.value = completedRes.data
    categories.value = categoriesRes.data
    logger.info('habit_stats_loaded', { completions: completedRes.data.length, categories: categoriesRes.data.length })
  } catch (e) {
    const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
    error.value = apiError
    notify('Failed to load habit stats', 'error')
    logger.error('habit_stats_load_failed', { detail: apiError.detail })
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
