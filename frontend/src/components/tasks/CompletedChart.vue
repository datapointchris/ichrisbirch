<template>
  <div class="completed-task-graph">
    <Bar
      :data="chartData"
      :options="chartOptions"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import { Chart as ChartJS, BarElement, CategoryScale, LinearScale, Title, Tooltip, Legend } from 'chart.js'
import type { CompletedTask } from '@/stores/tasks'
import { addDays, dayKeyOf } from '@/composables/calendarDay'

ChartJS.register(BarElement, CategoryScale, LinearScale, Title, Tooltip, Legend)

const props = defineProps<{ tasks: CompletedTask[] }>()

// A label names a day key, so it is printed on the UTC clock the key was placed on.
const DATE_FORMAT: Intl.DateTimeFormatOptions = { weekday: 'long', year: 'numeric', month: 'long', day: '2-digit', timeZone: 'UTC' }

const dataBarColors = [
  'rgba(255, 99, 132, 0.2)',
  'rgba(255, 159, 64, 0.2)',
  'rgba(255, 205, 86, 0.2)',
  'rgba(75, 192, 192, 0.2)',
  'rgba(54, 162, 235, 0.2)',
  'rgba(153, 102, 255, 0.2)',
  'rgba(201, 203, 207, 0.2)',
]

const chartData = computed(() => {
  if (props.tasks.length === 0) return { labels: [], datasets: [] }

  const days = props.tasks.map((task) => dayKeyOf(task.complete_date)).sort()
  const lastDay = days[days.length - 1]!

  const dayCount = new Map<string, number>()
  for (let day = days[0]!; day <= lastDay; day = addDays(day, 1)) {
    dayCount.set(day, 0)
  }
  for (const day of days) {
    dayCount.set(day, (dayCount.get(day) ?? 0) + 1)
  }

  const labels = [...dayCount.keys()].map((day) => new Date(`${day}T00:00:00Z`).toLocaleDateString('en-US', DATE_FORMAT))
  const values = [...dayCount.values()]

  return {
    labels,
    datasets: [
      {
        label: 'Completed Tasks',
        data: values,
        backgroundColor: dataBarColors,
      },
    ],
  }
})

const chartOptions = computed(() => {
  const textColor = 'hsl(0 0% 85%)'
  const gridColor = 'hsl(0 0% 35%)'
  const data = chartData.value.datasets[0]?.data ?? [1]
  const maxVal = Math.max(...data)

  return {
    responsive: true,
    scales: {
      y: {
        beginAtZero: true,
        max: Math.ceil(maxVal * 1.3),
        grid: { color: gridColor },
        ticks: { color: textColor, stepSize: 1, font: { size: 20 } },
      },
      x: {
        grid: { color: gridColor },
        ticks: { color: textColor, font: { size: 20 } },
      },
    },
    layout: { padding: { left: 20, right: 20, bottom: 20 } },
    plugins: {
      legend: { display: false },
      title: {
        display: true,
        text: 'Completed Tasks',
        color: textColor,
        font: { size: 20 },
        padding: 40,
      },
    },
  }
})
</script>
