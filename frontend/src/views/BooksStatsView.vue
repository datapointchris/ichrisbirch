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
            :data="readByMonthChartData"
            :options="readByMonthOptions"
          />
        </div>

        <div class="stats-chart">
          <Bar
            :data="byRatingChartData"
            :options="byRatingOptions"
          />
        </div>

        <StatsTable
          :headers="['Title', 'Author', 'Rating']"
          :empty="highestRated.length === 0"
        >
          <template #title>Highest Rated Books</template>
          <template #empty>No rated books.</template>
          <StatsTableRow
            v-for="book in highestRated"
            :key="book.title"
          >
            <span class="stats-name">{{ book.title }}</span>
            <span class="stats-meta">{{ book.author }}</span>
            <span class="stats-highlight">{{ book.rating }}/10</span>
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
import { paletteColors, verticalBarOptions, countByMonth, countByLabel, average } from '@/composables/useStatsCharts'
import type { Book } from '@/api/client'
import type { StatsCard } from '@/components/stats/StatsSummaryCards.vue'
import AppSubnav from '@/components/AppSubnav.vue'
import { BOOKS_SUBNAV } from '@/config/subnavLinks'
import StatsSummaryCards from '@/components/stats/StatsSummaryCards.vue'

const subnavLinks = BOOKS_SUBNAV
import StatsTable from '@/components/stats/StatsTable.vue'
import StatsTableRow from '@/components/stats/StatsTableRow.vue'

const logger = createLogger('BooksStats')
const { show: notify } = useNotifications()

const books = ref<Book[]>([])
const loading = ref(false)
const error = ref<ApiError | null>(null)

const loaded = computed(() => books.value.length > 0)

const summaryCards = computed<StatsCard[]>(() => {
  const all = books.value
  const rated = all.filter((b) => b.rating != null)
  const avgRating = average(rated.map((b) => b.rating!))
  return [
    { label: 'Total', value: all.length },
    { label: 'Read', value: all.filter((b) => b.progress === 'Read').length },
    { label: 'Reading', value: all.filter((b) => b.progress === 'Reading').length },
    { label: 'Unread', value: all.filter((b) => b.progress === 'Unread').length },
    { label: 'Abandoned', value: all.filter((b) => b.progress === 'abandoned').length },
    { label: 'Avg Rating', value: avgRating },
  ]
})

const readByMonthData = computed(() =>
  countByMonth(
    books.value.filter((b) => b.read_finish_date),
    (b) => b.read_finish_date
  )
)

const readByMonthChartData = computed(() => {
  if (readByMonthData.value.length === 0) return { labels: [], datasets: [] }
  const rows = readByMonthData.value
  return {
    labels: rows.map((r) => r.month),
    datasets: [{ label: 'Books Read', data: rows.map((r) => r.count), backgroundColor: paletteColors(rows.length) }],
  }
})

const readByMonthOptions = computed(() => {
  const data = readByMonthChartData.value.datasets[0]?.data ?? [1]
  return verticalBarOptions('Books Read per Month', data)
})

const byRatingData = computed(() =>
  countByLabel(
    books.value.filter((b) => b.rating != null),
    (b) => String(b.rating)
  ).sort((a, b) => Number(a.label) - Number(b.label))
)

const byRatingChartData = computed(() => {
  if (byRatingData.value.length === 0) return { labels: [], datasets: [] }
  const rows = byRatingData.value
  return {
    labels: rows.map((r) => r.label),
    datasets: [{ label: 'Count', data: rows.map((r) => r.count), backgroundColor: paletteColors(rows.length) }],
  }
})

const byRatingOptions = computed(() => {
  const data = byRatingChartData.value.datasets[0]?.data ?? [1]
  return verticalBarOptions('Rating Distribution', data)
})

const highestRated = computed(() =>
  books.value
    .filter((b) => b.rating != null)
    .sort((a, b) => (b.rating ?? 0) - (a.rating ?? 0))
    .slice(0, 10)
)

onMounted(async () => {
  loading.value = true
  try {
    const response = await api.get<Book[]>('/books/')
    books.value = response.data
    logger.info('book_stats_loaded', { count: response.data.length })
  } catch (e) {
    const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
    error.value = apiError
    notify('Failed to load book stats', 'error')
    logger.error('book_stats_load_failed', { detail: apiError.detail })
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
