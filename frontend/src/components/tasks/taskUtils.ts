import type { CompletedTask } from '@/stores/tasks'

export function daysToComplete(task: CompletedTask): number {
  const add = new Date(task.add_date)
  const complete = new Date(task.complete_date)
  return Math.max(Math.round((complete.getTime() - add.getTime()) / (1000 * 60 * 60 * 24)), 1)
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
