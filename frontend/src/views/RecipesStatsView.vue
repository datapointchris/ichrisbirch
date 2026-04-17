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

      <template v-else-if="stats">
        <StatsSummaryCards :cards="summaryCards" />

        <div
          v-if="cuisineChartData.labels.length > 0"
          class="stats-chart"
        >
          <Bar
            :data="cuisineChartData"
            :options="cuisineOptions"
          />
        </div>

        <div
          v-if="ratingChartData.labels.length > 0"
          class="stats-chart"
        >
          <Bar
            :data="ratingChartData"
            :options="ratingOptions"
          />
        </div>

        <StatsTable
          :headers="['Recipe', 'Cuisine', 'Made']"
          :empty="stats.most_made.length === 0"
        >
          <template #title>Most Made</template>
          <template #empty>No recipes made yet.</template>
          <StatsTableRow
            v-for="r in stats.most_made"
            :key="r.id"
          >
            <span class="stats-name">{{ r.name }}</span>
            <span class="stats-meta">{{ r.cuisine ?? '' }}</span>
            <span class="stats-highlight">{{ r.times_made }}×</span>
          </StatsTableRow>
        </StatsTable>

        <StatsTable
          :headers="['Recipe', 'Cuisine', 'Rating']"
          :empty="stats.highest_rated.length === 0"
        >
          <template #title>Highest Rated</template>
          <template #empty>No rated recipes.</template>
          <StatsTableRow
            v-for="r in stats.highest_rated"
            :key="r.id"
          >
            <span class="stats-name">{{ r.name }}</span>
            <span class="stats-meta">{{ r.cuisine ?? '' }}</span>
            <span class="stats-highlight">{{ r.rating }}/5</span>
          </StatsTableRow>
        </StatsTable>

        <StatsTable
          :headers="['Recipe', 'Cuisine', 'Added']"
          :empty="stats.untried.length === 0"
        >
          <template #title>Untried</template>
          <template #empty>Nothing untried — you've tried them all!</template>
          <StatsTableRow
            v-for="r in stats.untried"
            :key="r.id"
          >
            <span class="stats-name">{{ r.name }}</span>
            <span class="stats-meta">{{ r.cuisine ?? '' }}</span>
            <span class="stats-highlight">{{ formatDate(r.created_at, 'shortDate') }}</span>
          </StatsTableRow>
        </StatsTable>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Bar } from 'vue-chartjs'
import { ApiError } from '@/api/errors'
import { createLogger } from '@/utils/logger'
import { useNotifications } from '@/composables/useNotifications'
import { paletteColors, verticalBarOptions } from '@/composables/useStatsCharts'
import { formatDate } from '@/composables/formatDate'
import type { RecipeStats } from '@/api/client'
import type { StatsCard } from '@/components/stats/StatsSummaryCards.vue'
import AppSubnav from '@/components/AppSubnav.vue'
import StatsSummaryCards from '@/components/stats/StatsSummaryCards.vue'
import StatsTable from '@/components/stats/StatsTable.vue'
import StatsTableRow from '@/components/stats/StatsTableRow.vue'
import { useRecipesStore } from '@/stores/recipes'
import { RECIPES_SUBNAV } from '@/config/subnavLinks'

const subnavLinks = RECIPES_SUBNAV

const logger = createLogger('RecipesStats')
const { show: notify } = useNotifications()
const store = useRecipesStore()

const stats = ref<RecipeStats | null>(null)
const loading = ref(false)
const error = ref<ApiError | null>(null)

const summaryCards = computed<StatsCard[]>(() => {
  if (!stats.value) return []
  const s = stats.value
  return [
    { label: 'Total', value: s.total_recipes },
    { label: 'Times Cooked', value: s.total_times_cooked },
    { label: 'Avg Rating', value: s.average_rating !== null ? s.average_rating.toFixed(1) : '—' },
    { label: 'Cuisines', value: s.unique_cuisines },
  ]
})

const cuisineChartData = computed(() => {
  if (!stats.value) return { labels: [], datasets: [] }
  const rows = stats.value.cuisine_breakdown
  return {
    labels: rows.map((r) => r.name),
    datasets: [{ label: 'Recipes', data: rows.map((r) => r.count), backgroundColor: paletteColors(rows.length) }],
  }
})

const cuisineOptions = computed(() => {
  const data = cuisineChartData.value.datasets[0]?.data ?? [1]
  return verticalBarOptions('Recipes by Cuisine', data)
})

const ratingChartData = computed(() => {
  if (!stats.value) return { labels: [], datasets: [] }
  const rows = stats.value.rating_breakdown
  return {
    labels: rows.map((r) => `${r.rating} ★`),
    datasets: [{ label: 'Count', data: rows.map((r) => r.count), backgroundColor: paletteColors(rows.length) }],
  }
})

const ratingOptions = computed(() => {
  const data = ratingChartData.value.datasets[0]?.data ?? [1]
  return verticalBarOptions('Rating Distribution', data)
})

onMounted(async () => {
  loading.value = true
  try {
    stats.value = await store.fetchStats()
    logger.info('recipe_stats_loaded')
  } catch (e) {
    const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
    error.value = apiError
    notify('Failed to load recipe stats', 'error')
    logger.error('recipe_stats_load_failed', { detail: apiError.detail })
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
  text-transform: capitalize;
}

.stats-meta {
  color: var(--clr-gray-400);
  font-size: var(--fs-300);
  white-space: nowrap;
  text-transform: capitalize;
}

.stats-highlight {
  font-size: var(--fs-500);
  font-weight: 700;
  color: var(--clr-accent);
  text-align: right;
  white-space: nowrap;
}
</style>
