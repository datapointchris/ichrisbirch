import { describe, it, expect } from 'vitest'
import {
  addDays,
  dayKeyOf,
  daysBetween,
  endOfMonth,
  isCalendarDay,
  isReading,
  monthKeyOf,
  startOfMonth,
  startOfWeek,
  todayKey,
} from '../calendarDay'

// 21:00 on 20 August in New York, which is already the 21st in UTC.
const NEW_YORK_EVENING = '2026-08-21T01:00:00Z'

describe('dayKeyOf', () => {
  it('reads an instant on the calendar of the zone it is given', () => {
    expect(dayKeyOf(NEW_YORK_EVENING, 'America/New_York')).toBe('2026-08-20')
    expect(dayKeyOf(NEW_YORK_EVENING, 'UTC')).toBe('2026-08-21')
    expect(dayKeyOf(NEW_YORK_EVENING, 'Asia/Tokyo')).toBe('2026-08-21')
  })

  it('returns a stored day as it is, whatever the zone', () => {
    expect(dayKeyOf('2026-08-20', 'Pacific/Auckland')).toBe('2026-08-20')
    expect(dayKeyOf('2026-08-20', 'Pacific/Honolulu')).toBe('2026-08-20')
  })

  it('reads a wall clock by the day written in it', () => {
    expect(dayKeyOf('2026-08-20T23:30:00', 'Asia/Tokyo')).toBe('2026-08-20')
  })

  it('takes epoch milliseconds and Dates', () => {
    const instant = Date.parse(NEW_YORK_EVENING)
    expect(dayKeyOf(instant, 'America/New_York')).toBe('2026-08-20')
    expect(dayKeyOf(new Date(instant), 'America/New_York')).toBe('2026-08-20')
  })
})

describe('todayKey', () => {
  it('is the day now falls on in the zone', () => {
    const now = Date.parse(NEW_YORK_EVENING)
    expect(todayKey('America/New_York', now)).toBe('2026-08-20')
    expect(todayKey('UTC', now)).toBe('2026-08-21')
  })
})

describe('isReading', () => {
  it('tells a value with no offset from an instant', () => {
    expect(isReading('2026-08-20')).toBe(true)
    expect(isReading('2026-08-20T19:00:00')).toBe(true)
    expect(isReading('2026-08-20T19:00:00.123456')).toBe(true)
    expect(isReading('2026-08-20T19:00:00Z')).toBe(false)
    expect(isReading('2026-08-20T19:00:00-04:00')).toBe(false)
  })
})

describe('day arithmetic', () => {
  it('counts whole days across a spring-forward night', () => {
    // 8 March 2026 is 23 hours long in New York. Flooring elapsed milliseconds
    // over a day counts the 9th as 0 days after the 8th.
    expect(daysBetween('2026-03-08', '2026-03-09')).toBe(1)
    expect(daysBetween('2026-03-01', '2026-04-01')).toBe(31)
  })

  it('counts whole days across a fall-back night', () => {
    expect(daysBetween('2026-11-01', '2026-11-02')).toBe(1)
  })

  it('is negative when the second day is earlier', () => {
    expect(daysBetween('2026-08-20', '2026-08-18')).toBe(-2)
  })

  it('adds days across month and year ends', () => {
    expect(addDays('2026-12-31', 1)).toBe('2027-01-01')
    expect(addDays('2026-03-01', -1)).toBe('2026-02-28')
    expect(addDays('2028-03-01', -1)).toBe('2028-02-29')
  })

  it('opens a week on Monday', () => {
    expect(startOfWeek('2026-09-20')).toBe('2026-09-14')
    expect(startOfWeek('2026-09-21')).toBe('2026-09-21')
    expect(startOfWeek('2026-09-23')).toBe('2026-09-21')
  })

  it('finds the first and last day of a month', () => {
    expect(startOfMonth('2026-02-17')).toBe('2026-02-01')
    expect(endOfMonth('2026-02-17')).toBe('2026-02-28')
    expect(endOfMonth('2028-02-03')).toBe('2028-02-29')
    expect(endOfMonth('2026-12-05')).toBe('2026-12-31')
  })

  it('reads the month an instant falls in, in the zone', () => {
    expect(monthKeyOf('2026-09-01T02:00:00Z', 'America/New_York')).toBe('2026-08')
    expect(monthKeyOf('2026-09-01T02:00:00Z', 'UTC')).toBe('2026-09')
  })
})

describe('isCalendarDay', () => {
  it('refuses a day that rolls over into the next month', () => {
    expect(isCalendarDay('2026-02-28')).toBe(true)
    expect(isCalendarDay('2026-02-31')).toBe(false)
    expect(isCalendarDay('2026-13-01')).toBe(false)
    expect(isCalendarDay('2026-9-1')).toBe(false)
  })
})
