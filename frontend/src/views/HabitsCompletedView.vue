<template>
  <div>
    <HabitsSubnav active="completed" />

    <!-- Filter Controls -->
    <div class="grid grid--one-column grid--tight">
      <div class="grid__item">
        <form
          class="habits-completed__filters"
          @submit.prevent="handleFilter"
        >
          <div class="habits-completed__radio-group">
            <label
              v-for="filter in DATE_FILTERS"
              :key="filter"
              class="habits-completed__radio"
              :class="{ 'habits-completed__radio--selected': store.selectedFilter === filter }"
            >
              <input
                v-model="store.selectedFilter"
                type="radio"
                :value="filter"
                class="habits-completed__radio-input"
              />
              {{ formatFilterLabel(filter) }}
            </label>
          </div>
          <button
            type="submit"
            class="button"
          >
            <span class="button__text">Filter</span>
          </button>
        </form>
      </div>
    </div>

    <!-- Count -->
    <div class="grid grid--one-column grid--tight">
      <div class="grid__item">
        <p
          v-if="store.completedHabits.length > 0"
          class="habits-completed__count"
        >
          {{ store.completedHabits.length }} completed habits
        </p>
        <p
          v-else
          class="habits-completed__count habits-completed__count--empty"
        >
          No completed habits for: {{ formatFilterLabel(store.selectedFilter) }}
        </p>
      </div>
    </div>

    <!-- Chart -->
    <div
      v-if="store.chartData.labels.length > 0"
      class="grid grid--one-column"
    >
      <div class="grid__item habits-completed__chart-wrapper">
        <Bar
          :data="barChartData"
          :options="chartOptions"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { Bar } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, type ChartOptions } from 'chart.js'
import { useHabitsStore, DATE_FILTERS } from '@/stores/habits'
import { useNotifications } from '@/composables/useNotifications'
import { ApiError } from '@/api/errors'
import HabitsSubnav from '@/components/HabitsSubnav.vue'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip)

const store = useHabitsStore()
const { show: notify } = useNotifications()

const barChartData = computed(() => ({
  labels: store.chartData.labels,
  datasets: [
    {
      label: 'Habits Completed',
      data: store.chartData.values,
      backgroundColor: 'rgba(99, 102, 241, 0.6)',
      borderColor: 'rgba(99, 102, 241, 1)',
      borderWidth: 1,
    },
  ],
}))

const chartOptions: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    y: {
      beginAtZero: true,
      ticks: { stepSize: 1, color: '#9ca3af' },
      grid: { color: 'rgba(75, 85, 99, 0.3)' },
    },
    x: {
      ticks: { color: '#9ca3af', maxRotation: 45 },
      grid: { display: false },
    },
  },
  plugins: {
    tooltip: {
      callbacks: {
        label: (item) => `${item.parsed.y ?? 0} habits`,
      },
    },
  },
}

function formatFilterLabel(filter: string): string {
  return filter
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

onMounted(async () => {
  try {
    await store.fetchCompletedFiltered()
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to load completed habits: ${detail}`, 'error')
  }
})

async function handleFilter() {
  try {
    await store.fetchCompletedFiltered()
  } catch (e) {
    const detail = e instanceof ApiError ? e.userMessage : String(e)
    notify(`Failed to filter habits: ${detail}`, 'error')
  }
}
</script>

<style scoped>
.habits-completed__filters {
  display: flex;
  align-items: center;
  gap: var(--space-s);
  flex-wrap: wrap;
}

.habits-completed__radio-group {
  display: flex;
  gap: var(--space-xs);
  flex-wrap: wrap;
}

.habits-completed__radio {
  display: flex;
  align-items: center;
  gap: var(--space-3xs);
  padding: var(--space-3xs) var(--space-xs);
  border-radius: 4px;
  cursor: pointer;
  font-size: var(--fs-300);
  color: var(--clr-gray-400);
  transition: all 0.15s;
}

.habits-completed__radio:hover {
  color: var(--clr-gray-200);
}

.habits-completed__radio--selected {
  color: var(--clr-primary-300);
  background-color: color-mix(in srgb, var(--clr-primary-400) 15%, transparent);
}

.habits-completed__radio-input {
  accent-color: var(--clr-primary-400);
}

.habits-completed__count {
  font-size: var(--fs-500);
  font-weight: 600;
  color: var(--clr-primary-300);
}

.habits-completed__count--empty {
  color: var(--clr-gray-400);
  font-weight: 400;
  font-style: italic;
}

.habits-completed__chart-wrapper {
  height: 400px;
  min-height: 300px;
}
</style>
