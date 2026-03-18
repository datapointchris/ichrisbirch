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

ChartJS.register(BarElement, CategoryScale, LinearScale, Title, Tooltip, Legend)

const props = defineProps<{ tasks: CompletedTask[] }>()

const DATE_FORMAT: Intl.DateTimeFormatOptions = { weekday: 'long', year: 'numeric', month: 'long', day: '2-digit' }

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

  const sorted = [...props.tasks].sort((a, b) => new Date(a.complete_date).getTime() - new Date(b.complete_date).getTime())

  const first = new Date(sorted[0]!.complete_date)
  const last = new Date(sorted[sorted.length - 1]!.complete_date)

  const dayCount: Record<string, number> = {}
  const current = new Date(first.getFullYear(), first.getMonth(), first.getDate())
  const end = new Date(last.getFullYear(), last.getMonth(), last.getDate())
  end.setDate(end.getDate() + 1)

  while (current <= end) {
    dayCount[current.toISOString().slice(0, 10)] = 0
    current.setDate(current.getDate() + 1)
  }

  for (const task of sorted) {
    const key = new Date(task.complete_date).toISOString().slice(0, 10)
    if (key in dayCount) dayCount[key] = (dayCount[key] ?? 0) + 1
  }

  const entries = Object.entries(dayCount)
  const labels = entries.map(([dateStr]) => new Date(dateStr + 'T12:00:00').toLocaleDateString('en-US', DATE_FORMAT))
  const values = entries.map(([, count]) => count)

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
