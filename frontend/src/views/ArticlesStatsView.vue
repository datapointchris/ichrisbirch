<template>
  <div>
    <ArticlesSubnav />

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
            :data="byTagChartData"
            :options="byTagOptions"
          />
        </div>

        <div class="stats-chart">
          <Bar
            :data="savedByMonthChartData"
            :options="savedByMonthOptions"
          />
        </div>

        <StatsTable
          :headers="['Title', 'Tags', 'Times Read']"
          :empty="frequentlyRead.length === 0"
        >
          <template #title>Read More Than Once</template>
          <template #empty>No articles read more than once yet.</template>
          <StatsTableRow
            v-for="article in frequentlyRead"
            :key="article.id"
          >
            <a
              :href="article.url"
              target="_blank"
              class="stats-link"
              >{{ article.title }}</a
            >
            <span class="stats-meta">{{ article.tags.join(', ') }}</span>
            <span class="stats-highlight">{{ article.read_count }}</span>
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
import { getThemeColors, paletteColors, horizontalBarOptions, verticalBarOptions, countByMonth } from '@/composables/useStatsCharts'
import type { Article } from '@/api/client'
import type { StatsCard } from '@/components/stats/StatsSummaryCards.vue'
import ArticlesSubnav from '@/components/ArticlesSubnav.vue'
import StatsSummaryCards from '@/components/stats/StatsSummaryCards.vue'
import StatsTable from '@/components/stats/StatsTable.vue'
import StatsTableRow from '@/components/stats/StatsTableRow.vue'

const logger = createLogger('ArticlesStats')
const { show: notify } = useNotifications()

const articles = ref<Article[]>([])
const loading = ref(false)
const error = ref<ApiError | null>(null)

const loaded = computed(() => articles.value.length > 0)

const TOP_TAGS = 30

const summaryCards = computed<StatsCard[]>(() => {
  const all = articles.value
  const read = all.filter((a) => a.read_count > 0).length
  return [
    { label: 'Total', value: all.length },
    { label: 'Read', value: read },
    { label: 'Unread', value: all.length - read },
    { label: 'Favorites', value: all.filter((a) => a.is_favorite).length },
    { label: 'Archived', value: all.filter((a) => a.is_archived).length },
  ]
})

const tagBreakdown = computed(() => {
  const tags = new Map<string, { total: number; read: number; unread: number }>()
  for (const article of articles.value) {
    for (const tag of article.tags) {
      const entry = tags.get(tag) ?? { total: 0, read: 0, unread: 0 }
      entry.total++
      if (article.read_count > 0) entry.read++
      else entry.unread++
      tags.set(tag, entry)
    }
  }
  return [...tags.entries()]
    .sort(([, a], [, b]) => b.total - a.total)
    .slice(0, TOP_TAGS)
    .map(([tag, d]) => ({ tag, ...d }))
})

const byTagChartData = computed(() => {
  if (tagBreakdown.value.length === 0) return { labels: [], datasets: [] }
  const rows = tagBreakdown.value
  return {
    labels: rows.map((r) => r.tag),
    datasets: [
      { label: 'Read', data: rows.map((r) => r.read), backgroundColor: getThemeColors().primary, stack: 'stack' },
      { label: 'Unread', data: rows.map((r) => r.unread), backgroundColor: getThemeColors().secondary, stack: 'stack' },
    ],
  }
})

const byTagOptions = computed(() =>
  horizontalBarOptions(`Articles by Tag — Read vs Unread (top ${TOP_TAGS})`, { stacked: true, legend: true })
)

const savedByMonthData = computed(() => countByMonth(articles.value, (a) => a.save_date))

const savedByMonthChartData = computed(() => {
  if (savedByMonthData.value.length === 0) return { labels: [], datasets: [] }
  const rows = savedByMonthData.value
  return {
    labels: rows.map((r) => r.month),
    datasets: [{ label: 'Articles Saved', data: rows.map((r) => r.count), backgroundColor: paletteColors(rows.length) }],
  }
})

const savedByMonthOptions = computed(() => {
  const data = savedByMonthChartData.value.datasets[0]?.data ?? [1]
  return verticalBarOptions('Articles Saved per Month', data)
})

const frequentlyRead = computed(() =>
  articles.value
    .filter((a) => a.read_count > 1)
    .sort((a, b) => b.read_count - a.read_count)
    .slice(0, 20)
)

onMounted(async () => {
  loading.value = true
  try {
    const response = await api.get<Article[]>('/articles/')
    articles.value = response.data
    logger.info('article_stats_loaded', { count: response.data.length })
  } catch (e) {
    const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
    error.value = apiError
    notify('Failed to load article stats', 'error')
    logger.error('article_stats_load_failed', { detail: apiError.detail })
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

.stats-link {
  color: var(--clr-primary-300);
  text-decoration: none;
  font-size: var(--fs-400);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stats-link:hover {
  color: var(--clr-primary-200);
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
