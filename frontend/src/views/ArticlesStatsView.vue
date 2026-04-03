<template>
  <div>
    <ArticlesSubnav active="stats" />

    <div class="grid grid--one-column">
      <div
        v-if="loading"
        class="articles-stats__empty"
      >
        Loading...
      </div>

      <div
        v-else-if="error"
        class="articles-stats__empty"
      >
        {{ error.userMessage }}
      </div>

      <template v-else-if="stats">
        <!-- Summary Cards -->
        <div class="articles-stats__summary">
          <div
            v-for="card in summaryCards"
            :key="card.label"
            class="articles-stats__card"
          >
            <div class="articles-stats__card-value">{{ card.value }}</div>
            <div class="articles-stats__card-label">{{ card.label }}</div>
          </div>
        </div>

        <!-- Articles by Tag (stacked: read vs unread) -->
        <div class="articles-stats__chart-wrapper">
          <Bar
            :data="byTagChartData"
            :options="byTagOptions"
          />
        </div>

        <!-- Articles Saved per Month -->
        <div class="articles-stats__chart-wrapper">
          <Bar
            :data="savedByMonthChartData"
            :options="savedByMonthOptions"
          />
        </div>

        <!-- Frequently Read Articles -->
        <div class="articles-stats__frequently-read">
          <h3 class="articles-stats__section-title">Read More Than Once</h3>
          <div
            v-if="stats.frequently_read.length === 0"
            class="articles-stats__empty"
          >
            No articles read more than once yet.
          </div>
          <template v-else>
            <div class="articles-stats__freq-header">
              <span>Title</span>
              <span>Tags</span>
              <span>Times Read</span>
            </div>
            <div
              v-for="article in stats.frequently_read"
              :key="article.id"
              class="articles-stats__freq-row"
            >
              <a
                :href="article.url"
                target="_blank"
                class="articles-stats__freq-title"
                >{{ article.title }}</a
              >
              <span class="articles-stats__freq-tags">{{ article.tags.join(', ') }}</span>
              <span class="articles-stats__freq-count">{{ article.read_count }}</span>
            </div>
          </template>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Bar } from 'vue-chartjs'
import { Chart as ChartJS, BarElement, CategoryScale, LinearScale, Title, Tooltip, Legend } from 'chart.js'
import { api } from '@/api/client'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import { useNotifications } from '@/composables/useNotifications'
import type { ArticleStats } from '@/api/client'
import ArticlesSubnav from '@/components/ArticlesSubnav.vue'

ChartJS.register(BarElement, CategoryScale, LinearScale, Title, Tooltip, Legend)

const logger = createLogger('ArticlesStats')
const { show: notify } = useNotifications()

const stats = ref<ArticleStats | null>(null)
const loading = ref(false)
const error = ref<ApiError | null>(null)

const TEXT_COLOR = 'hsl(0 0% 85%)'
const GRID_COLOR = 'hsl(0 0% 35%)'
const COLOR_READ = 'rgba(54, 162, 235, 0.7)'
const COLOR_UNREAD = 'rgba(201, 203, 207, 0.35)'
const BAR_COLORS = [
  'rgba(255, 99, 132, 0.6)',
  'rgba(255, 159, 64, 0.6)',
  'rgba(255, 205, 86, 0.6)',
  'rgba(75, 192, 192, 0.6)',
  'rgba(54, 162, 235, 0.6)',
  'rgba(153, 102, 255, 0.6)',
  'rgba(201, 203, 207, 0.6)',
]

const TOP_TAGS = 30

const summaryCards = computed(() => {
  if (!stats.value) return []
  const s = stats.value.summary
  return [
    { label: 'Total', value: s.total },
    { label: 'Read', value: s.read },
    { label: 'Unread', value: s.unread },
    { label: 'Favorites', value: s.favorites },
    { label: 'Archived', value: s.archived },
  ]
})

// Stacked horizontal bar: read (blue) + unread (gray) per tag
const byTagChartData = computed(() => {
  if (!stats.value || stats.value.by_tag.length === 0) return { labels: [], datasets: [] }
  const top = stats.value.by_tag.slice(0, TOP_TAGS)
  const labels = top.map((r) => r.tag)
  return {
    labels,
    datasets: [
      { label: 'Read', data: top.map((r) => r.read), backgroundColor: COLOR_READ, stack: 'stack' },
      { label: 'Unread', data: top.map((r) => r.unread), backgroundColor: COLOR_UNREAD, stack: 'stack' },
    ],
  }
})

const byTagOptions = computed(() => ({
  indexAxis: 'y' as const,
  responsive: true,
  scales: {
    x: {
      stacked: true,
      grid: { color: GRID_COLOR },
      ticks: { color: TEXT_COLOR, stepSize: 1, font: { size: 14 } },
    },
    y: {
      stacked: true,
      grid: { color: GRID_COLOR },
      ticks: { color: TEXT_COLOR, font: { size: 13 } },
    },
  },
  layout: { padding: { left: 20, right: 20, bottom: 20 } },
  plugins: {
    legend: {
      display: true,
      labels: { color: TEXT_COLOR, font: { size: 14 } },
    },
    title: {
      display: true,
      text: `Articles by Tag — Read vs Unread (top ${TOP_TAGS})`,
      color: TEXT_COLOR,
      font: { size: 20 },
      padding: 40,
    },
  },
}))

// Vertical bar: articles saved per month
const savedByMonthChartData = computed(() => {
  if (!stats.value || stats.value.saved_by_month.length === 0) return { labels: [], datasets: [] }
  const rows = stats.value.saved_by_month
  return {
    labels: rows.map((r) => r.month),
    datasets: [
      {
        label: 'Articles Saved',
        data: rows.map((r) => r.count),
        backgroundColor: rows.map((_, i) => BAR_COLORS[i % BAR_COLORS.length]!),
      },
    ],
  }
})

const savedByMonthOptions = computed(() => {
  const data = savedByMonthChartData.value.datasets[0]?.data ?? [1]
  const maxVal = Math.max(...data)
  return {
    responsive: true,
    scales: {
      y: {
        beginAtZero: true,
        max: Math.ceil(maxVal * 1.3),
        grid: { color: GRID_COLOR },
        ticks: { color: TEXT_COLOR, stepSize: 1, font: { size: 14 } },
      },
      x: {
        grid: { color: GRID_COLOR },
        ticks: { color: TEXT_COLOR, font: { size: 13 } },
      },
    },
    layout: { padding: { left: 20, right: 20, bottom: 20 } },
    plugins: {
      legend: { display: false },
      title: {
        display: true,
        text: 'Articles Saved per Month',
        color: TEXT_COLOR,
        font: { size: 20 },
        padding: 40,
      },
    },
  }
})

onMounted(async () => {
  loading.value = true
  try {
    const response = await api.get<ArticleStats>('/articles/stats/')
    stats.value = response.data
    logger.info('article_stats_fetched', {
      total: response.data.summary.total,
      tags: response.data.by_tag.length,
    })
  } catch (e) {
    const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
    error.value = apiError
    notify('Failed to load article stats', 'error')
    logger.error('article_stats_fetch_failed', { detail: apiError.detail })
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.articles-stats__summary {
  display: flex;
  gap: var(--space-s);
  flex-wrap: wrap;
}

.articles-stats__card {
  flex: 1;
  min-width: 100px;
  padding: var(--space-s) var(--space-m);
  box-shadow: var(--floating-box);
  border-radius: var(--border-radius);
  text-align: center;
}

.articles-stats__card-value {
  font-size: var(--fs-700);
  font-weight: 700;
  color: var(--clr-primary-300);
}

.articles-stats__card-label {
  font-size: var(--fs-300);
  color: var(--clr-gray-400);
  margin-top: var(--space-3xs);
}

.articles-stats__chart-wrapper {
  padding: var(--space-m);
}

.articles-stats__empty {
  color: var(--clr-gray-500);
  font-style: italic;
}

.articles-stats__frequently-read {
  display: flex;
  flex-direction: column;
  gap: var(--space-2xs);
}

.articles-stats__section-title {
  font-size: var(--fs-500);
  color: var(--clr-gray-300);
  margin-bottom: var(--space-xs);
}

.articles-stats__freq-header,
.articles-stats__freq-row {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: var(--space-m);
  align-items: center;
  padding: var(--space-2xs) var(--space-s);
}

.articles-stats__freq-header {
  font-size: var(--fs-300);
  color: var(--clr-gray-500);
  border-bottom: 1px solid var(--clr-gray-700);
}

.articles-stats__freq-row {
  box-shadow: var(--floating-box);
  border-radius: var(--border-radius);
}

.articles-stats__freq-title {
  color: var(--clr-primary-300);
  text-decoration: none;
  font-size: var(--fs-400);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.articles-stats__freq-title:hover {
  color: var(--clr-primary-200);
}

.articles-stats__freq-tags {
  color: var(--clr-gray-400);
  font-size: var(--fs-300);
  white-space: nowrap;
}

.articles-stats__freq-count {
  font-size: var(--fs-500);
  font-weight: 700;
  color: var(--clr-accent);
  text-align: right;
  white-space: nowrap;
}
</style>
