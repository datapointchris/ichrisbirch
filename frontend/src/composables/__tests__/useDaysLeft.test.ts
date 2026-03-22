import { describe, it, expect, vi, afterEach } from 'vitest'
import { computeDaysLeft } from '../useDaysLeft'

// Use local-time Date constructors to avoid UTC parsing offset issues
function localDate(year: number, month: number, day: number): Date {
  return new Date(year, month - 1, day)
}

describe('computeDaysLeft', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('returns "Past" for dates in the past', () => {
    vi.useFakeTimers()
    vi.setSystemTime(localDate(2026, 6, 15))
    const result = computeDaysLeft('2026-06-01')
    expect(result.text).toBe('Past')
    expect(result.urgency).toBe('past')
    expect(result.totalDays).toBe(0)
  })

  it('returns "Past" for today', () => {
    vi.useFakeTimers()
    vi.setSystemTime(localDate(2026, 6, 15))
    const result = computeDaysLeft('2026-06-15')
    expect(result.text).toBe('Past')
    expect(result.urgency).toBe('past')
  })

  it('calculates days correctly', () => {
    vi.useFakeTimers()
    vi.setSystemTime(localDate(2026, 6, 15))
    const result = computeDaysLeft('2026-06-20')
    expect(result.text).toBe('5 days')
    expect(result.totalDays).toBe(5)
    expect(result.urgency).toBe('two-weeks')
  })

  it('calculates 1 day singular', () => {
    vi.useFakeTimers()
    vi.setSystemTime(localDate(2026, 6, 15))
    const result = computeDaysLeft('2026-06-16')
    expect(result.text).toBe('1 day')
  })

  it('calculates weeks and days', () => {
    vi.useFakeTimers()
    vi.setSystemTime(localDate(2026, 6, 1))
    const result = computeDaysLeft('2026-06-18')
    expect(result.text).toBe('2 weeks, 3 days')
    expect(result.urgency).toBe('month')
  })

  it('calculates months', () => {
    vi.useFakeTimers()
    vi.setSystemTime(localDate(2026, 1, 1))
    const result = computeDaysLeft('2026-03-15')
    expect(result.text).toContain('month')
    expect(result.urgency).toBe('none')
  })

  it('calculates years', () => {
    vi.useFakeTimers()
    vi.setSystemTime(localDate(2026, 1, 1))
    const result = computeDaysLeft('2028-06-15')
    expect(result.text).toContain('year')
    expect(result.urgency).toBe('none')
  })

  it('marks < 14 days as two-weeks urgency', () => {
    vi.useFakeTimers()
    vi.setSystemTime(localDate(2026, 6, 1))
    const result = computeDaysLeft('2026-06-10')
    expect(result.urgency).toBe('two-weeks')
  })

  it('marks 14-29 days as month urgency', () => {
    vi.useFakeTimers()
    vi.setSystemTime(localDate(2026, 6, 1))
    const result = computeDaysLeft('2026-06-25')
    expect(result.urgency).toBe('month')
  })

  it('marks >= 30 days as no urgency', () => {
    vi.useFakeTimers()
    vi.setSystemTime(localDate(2026, 6, 1))
    const result = computeDaysLeft('2026-07-15')
    expect(result.urgency).toBe('none')
  })
})
