import { describe, it, expect } from 'vitest'
import { daysToComplete, timeToComplete } from '../taskUtils'
import type { CompletedTask } from '@/stores/tasks'

function task(add_date: string, complete_date: string): CompletedTask {
  return { id: 1, name: 'Test', category: 'Chore', priority: 1, add_date, complete_date }
}

// Monday 08:00 to Tuesday 20:00 in New York: 36 hours, and one calendar day.
const MONDAY_MORNING = '2026-09-21T12:00:00Z'
const TUESDAY_EVENING = '2026-09-23T00:00:00Z'

describe('daysToComplete', () => {
  it('counts calendar days rather than 24-hour blocks', () => {
    expect(daysToComplete(task(MONDAY_MORNING, TUESDAY_EVENING), 'America/New_York')).toBe(1)
  })

  it('reads both ends on the calendar of the zone it is given', () => {
    expect(daysToComplete(task(MONDAY_MORNING, TUESDAY_EVENING), 'UTC')).toBe(2)
  })

  it('counts a task done the day it was added as 0', () => {
    expect(daysToComplete(task(MONDAY_MORNING, '2026-09-21T20:00:00Z'), 'America/New_York')).toBe(0)
  })
})

describe('timeToComplete', () => {
  it('formats days as weeks and remainder', () => {
    expect(timeToComplete(task('2026-02-01T00:00:00', '2026-03-01T00:00:00'))).toBe('4 weeks, 0 days')
  })

  it('handles partial weeks', () => {
    expect(timeToComplete(task('2026-01-01T00:00:00', '2026-01-12T00:00:00'))).toBe('1 weeks, 4 days')
  })
})
