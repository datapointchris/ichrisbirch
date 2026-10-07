import type { Task } from '@/api/client'
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

const DAY_MS = 24 * 60 * 60 * 1000

export interface DropPlacement {
  rankAt: string
  pinned: boolean
}

// Where a task dropped between `above` and `below` sorts. It takes the pinned
// state of the task below it, so a drop just under the pinned group stays out
// of it. A pinned neighbor never bounds an unpinned task, since pinned tasks
// sort first whatever their rank.
export function placementBetween(above: Task | undefined, below: Task | undefined): DropPlacement {
  const pinned = below ? below.pinned : (above?.pinned ?? false)
  const lower = above && above.pinned === pinned ? new Date(above.rank_at).getTime() : undefined
  const upper = below ? new Date(below.rank_at).getTime() : undefined

  let rankAt: number
  if (lower !== undefined && upper !== undefined) rankAt = lower + (upper - lower) / 2
  else if (upper !== undefined) rankAt = upper - DAY_MS
  else if (lower !== undefined) rankAt = lower + DAY_MS
  else rankAt = Date.now()

  return { rankAt: new Date(Math.round(rankAt)).toISOString(), pinned }
}

export function averageCompletionTime(tasks: CompletedTask[]): string {
  if (tasks.length === 0) return ''
  const totalDays = tasks.reduce((sum, t) => sum + daysToComplete(t), 0)
  const avg = totalDays / tasks.length
  const weeks = Math.floor(avg / 7)
  const days = Math.floor(avg % 7)
  return `${weeks} weeks, ${days} days`
}
