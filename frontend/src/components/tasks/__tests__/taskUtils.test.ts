import { describe, it, expect } from 'vitest'
import { daysToComplete, placementBetween, timeToComplete } from '../taskUtils'
import type { Task } from '@/api/client'
import type { CompletedTask } from '@/stores/tasks'

function task(add_date: string, complete_date: string): CompletedTask {
  return { id: 1, name: 'Test', category: 'Chore', rank_at: add_date, window_days: 30, pinned: false, add_date, complete_date }
}

function ranked(rank_at: string, pinned = false): Task {
  return { id: 1, name: 'Test', category: 'Chore', rank_at, window_days: 30, pinned, add_date: '2026-01-01T00:00:00Z' }
}

describe('placementBetween', () => {
  it('lands halfway between two neighbors', () => {
    const placement = placementBetween(ranked('2026-03-01T00:00:00Z'), ranked('2026-03-03T00:00:00Z'))
    expect(placement).toEqual({ rankAt: '2026-03-02T00:00:00.000Z', pinned: false })
  })

  it('lands a day ahead of the first task when dropped at the top', () => {
    expect(placementBetween(undefined, ranked('2026-03-03T00:00:00Z')).rankAt).toBe('2026-03-02T00:00:00.000Z')
  })

  it('lands a day behind the last task when dropped at the bottom', () => {
    expect(placementBetween(ranked('2026-03-03T00:00:00Z'), undefined).rankAt).toBe('2026-03-04T00:00:00.000Z')
  })

  it('takes the pinned state of the task below it', () => {
    expect(placementBetween(undefined, ranked('2026-09-01T00:00:00Z', true)).pinned).toBe(true)
    expect(placementBetween(ranked('2026-09-01T00:00:00Z', true), ranked('2026-03-03T00:00:00Z')).pinned).toBe(false)
  })

  it('ignores a pinned neighbor above as a bound for an unpinned drop', () => {
    const placement = placementBetween(ranked('2027-01-01T00:00:00Z', true), ranked('2026-03-03T00:00:00Z'))
    expect(placement.rankAt).toBe('2026-03-02T00:00:00.000Z')
  })

  it('stays pinned when dropped at the bottom of the pinned group with nothing below', () => {
    expect(placementBetween(ranked('2026-03-03T00:00:00Z', true), undefined)).toEqual({
      rankAt: '2026-03-04T00:00:00.000Z',
      pinned: true,
    })
  })
})

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
