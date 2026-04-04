<template>
  <div>
    <TasksSubnav />

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
            :data="avgTimeChartData"
            :options="avgTimeOptions"
          />
        </div>

        <StatsTable
          :headers="['Task', 'Category', 'Days Open']"
          :empty="longestOutstanding.length === 0"
        >
          <template #title>Longest Outstanding Tasks</template>
          <template #empty>No outstanding tasks.</template>
          <StatsTableRow
            v-for="task in longestOutstanding"
            :key="task.id"
          >
            <span class="stats-name">{{ task.name }}</span>
            <span class="stats-meta">{{ task.category }}</span>
            <span class="stats-highlight">{{ daysAgo(task.add_date) }}</span>
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
import {
  getThemeColors,
  paletteColors,
  horizontalBarOptions,
  verticalBarOptions,
  countByMonth,
  average,
  daysBetween,
  daysAgo,
} from '@/composables/useStatsCharts'
import type { Task } from '@/api/client'
import type { StatsCard } from '@/components/stats/StatsSummaryCards.vue'
import TasksSubnav from '@/components/tasks/TasksSubnav.vue'
import StatsSummaryCards from '@/components/stats/StatsSummaryCards.vue'
import StatsTable from '@/components/stats/StatsTable.vue'
import StatsTableRow from '@/components/stats/StatsTableRow.vue'

const logger = createLogger('TasksStats')
const { show: notify } = useNotifications()

const todoTasks = ref<Task[]>([])
const completedTasks = ref<Task[]>([])
const loading = ref(false)
const error = ref<ApiError | null>(null)

const loaded = computed(() => todoTasks.value.length > 0 || completedTasks.value.length > 0)

const summaryCards = computed<StatsCard[]>(() => {
  const todo = todoTasks.value
  const completed = completedTasks.value
  const avgDays = average(completed.filter((t) => t.complete_date).map((t) => daysBetween(t.add_date, t.complete_date!)))
  return [
    { label: 'Total (All Time)', value: todo.length + completed.length },
    { label: 'Completed (All Time)', value: completed.length },
    { label: 'Outstanding', value: todo.length },
    { label: 'Avg Days to Complete', value: avgDays },
    { label: 'Overdue', value: todo.filter((t) => t.priority < 1).length },
  ]
})

const categoryBreakdown = computed(() => {
  const cats = new Map<string, { completed: number; outstanding: number; totalDays: number; completedWithDays: number }>()
  for (const task of completedTasks.value) {
    const entry = cats.get(task.category) ?? { completed: 0, outstanding: 0, totalDays: 0, completedWithDays: 0 }
    entry.completed++
    if (task.complete_date) {
      entry.totalDays += daysBetween(task.add_date, task.complete_date)
      entry.completedWithDays++
    }
    cats.set(task.category, entry)
  }
  for (const task of todoTasks.value) {
    const entry = cats.get(task.category) ?? { completed: 0, outstanding: 0, totalDays: 0, completedWithDays: 0 }
    entry.outstanding++
    cats.set(task.category, entry)
  }
  return [...cats.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([category, d]) => ({
      category,
      completed: d.completed,
      outstanding: d.outstanding,
      avgDays: d.completedWithDays > 0 ? Math.round((d.totalDays / d.completedWithDays) * 10) / 10 : 0,
    }))
})

const byCategoryChartData = computed(() => {
  if (categoryBreakdown.value.length === 0) return { labels: [], datasets: [] }
  const rows = categoryBreakdown.value
  return {
    labels: rows.map((r) => r.category),
    datasets: [
      { label: 'Completed', data: rows.map((r) => r.completed), backgroundColor: getThemeColors().primary, stack: 'stack' },
      { label: 'Outstanding', data: rows.map((r) => r.outstanding), backgroundColor: getThemeColors().secondary, stack: 'stack' },
    ],
  }
})

const byCategoryOptions = computed(() =>
  horizontalBarOptions('Tasks by Category — Completed vs Outstanding', { stacked: true, legend: true })
)

const completedByMonthData = computed(() => countByMonth(completedTasks.value, (t) => t.complete_date))

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
  return verticalBarOptions('Tasks Completed per Month', data)
})

const avgTimeData = computed(() => categoryBreakdown.value.filter((r) => r.avgDays > 0))

const avgTimeChartData = computed(() => {
  if (avgTimeData.value.length === 0) return { labels: [], datasets: [] }
  return {
    labels: avgTimeData.value.map((r) => r.category),
    datasets: [
      {
        label: 'Avg Days to Complete',
        data: avgTimeData.value.map((r) => r.avgDays),
        backgroundColor: paletteColors(avgTimeData.value.length),
      },
    ],
  }
})

const avgTimeOptions = computed(() => horizontalBarOptions('Average Completion Time by Category (Days)'))

const longestOutstanding = computed(() =>
  [...todoTasks.value].sort((a, b) => new Date(a.add_date).getTime() - new Date(b.add_date).getTime()).slice(0, 10)
)

onMounted(async () => {
  loading.value = true
  try {
    const [todoRes, completedRes] = await Promise.all([api.get<Task[]>('/tasks/todo/'), api.get<Task[]>('/tasks/completed/')])
    todoTasks.value = todoRes.data
    completedTasks.value = completedRes.data
    logger.info('task_stats_loaded', { todo: todoRes.data.length, completed: completedRes.data.length })
  } catch (e) {
    const apiError = e instanceof ApiError ? e : new ApiError({ message: String(e), detail: String(e) })
    error.value = apiError
    notify('Failed to load task stats', 'error')
    logger.error('task_stats_load_failed', { detail: apiError.detail })
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
