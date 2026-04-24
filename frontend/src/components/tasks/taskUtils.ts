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

export type DateFilterKey = 'today' | 'yesterday' | 'this_week' | 'last_7' | 'this_month' | 'last_30' | 'this_year' | 'all'

export const DATE_FILTERS: DateFilterKey[] = ['today', 'yesterday', 'this_week', 'last_7', 'this_month', 'last_30', 'this_year', 'all']

export function dateFilterLabel(key: DateFilterKey): string {
  return key
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

function getWeekStart(d: Date): Date {
  const day = d.getDay()
  const diff = day === 0 ? 6 : day - 1
  const start = new Date(d)
  start.setDate(d.getDate() - diff)
  start.setHours(0, 0, 0, 0)
  return start
}

export function dateFilterRange(key: DateFilterKey): { start?: string; end?: string } {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)

  const fmt = (d: Date) => d.toISOString()

  switch (key) {
    case 'today':
      return { start: fmt(today), end: fmt(tomorrow) }
    case 'yesterday': {
      const yesterday = new Date(today)
      yesterday.setDate(yesterday.getDate() - 1)
      return { start: fmt(yesterday), end: fmt(today) }
    }
    case 'this_week': {
      const weekStart = getWeekStart(today)
      const weekEnd = new Date(weekStart)
      weekEnd.setDate(weekEnd.getDate() + 7)
      return { start: fmt(weekStart), end: fmt(weekEnd) }
    }
    case 'last_7': {
      const prev7 = new Date(today)
      prev7.setDate(prev7.getDate() - 7)
      return { start: fmt(prev7), end: fmt(tomorrow) }
    }
    case 'this_month': {
      const monthStart = new Date(today.getFullYear(), today.getMonth(), 1)
      const monthEnd = new Date(today.getFullYear(), today.getMonth() + 1, 1)
      return { start: fmt(monthStart), end: fmt(monthEnd) }
    }
    case 'last_30': {
      const prev30 = new Date(today)
      prev30.setDate(prev30.getDate() - 30)
      return { start: fmt(prev30), end: fmt(tomorrow) }
    }
    case 'this_year': {
      const yearStart = new Date(today.getFullYear(), 0, 1)
      const yearEnd = new Date(today.getFullYear() + 1, 0, 1)
      return { start: fmt(yearStart), end: fmt(yearEnd) }
    }
    case 'all':
      return {}
  }
}
