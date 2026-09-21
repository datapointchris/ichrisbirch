import type { CompletedTask } from '@/stores/tasks'
import { daysBetween } from '@/composables/calendarDay'
import { displayZone } from '@/composables/displayZone'

// `TasksStatsView` counts with `daysBetween` too, so both pages read a task done the day it was added as 0.
export function daysToComplete(task: CompletedTask, zone: string = displayZone()): number {
  return daysBetween(task.add_date, task.complete_date, zone)
}

export function timeToComplete(task: CompletedTask): string {
  const days = daysToComplete(task)
  const weeks = Math.floor(days / 7)
  const remainder = days % 7
  return `${weeks} weeks, ${remainder} days`
}

export function averageCompletionTime(tasks: CompletedTask[]): string {
  if (tasks.length === 0) return ''
  const totalDays = tasks.reduce((sum, t) => sum + daysToComplete(t), 0)
  const avg = totalDays / tasks.length
  const weeks = Math.floor(avg / 7)
  const days = Math.floor(avg % 7)
  return `${weeks} weeks, ${days} days`
}
