import { describe, it, expect, vi, afterEach } from 'vitest'
import { compareWallClocks, wallClockInstant, wallClockIsPast, browserTimezone } from '../useWallClock'

afterEach(() => vi.useRealTimers())

describe('wallClockInstant', () => {
  it('resolves a reading against the zone it was read in', () => {
    const utc = wallClockInstant({ date: '2026-09-28T09:00:00', timezone: 'UTC' })
    expect(new Date(utc).toISOString()).toBe('2026-09-28T09:00:00.000Z')
  })

  it('uses the zone offset in force on that date, not the one in force now', () => {
    // New York is -04:00 in September and -05:00 in January. A fixed offset would
    // put one of these an hour out.
    const summer = wallClockInstant({ date: '2026-09-28T12:00:00', timezone: 'America/New_York' })
    const winter = wallClockInstant({ date: '2026-01-28T12:00:00', timezone: 'America/New_York' })
    expect(new Date(summer).toISOString()).toBe('2026-09-28T16:00:00.000Z')
    expect(new Date(winter).toISOString()).toBe('2026-01-28T17:00:00.000Z')
  })

  it('accepts a bare day as midnight in its zone', () => {
    const instant = wallClockInstant({ date: '2026-09-28', timezone: 'UTC' })
    expect(new Date(instant).toISOString()).toBe('2026-09-28T00:00:00.000Z')
  })

  it('is NaN for a reading it cannot parse', () => {
    expect(wallClockInstant({ date: 'not a date', timezone: 'UTC' })).toBeNaN()
  })

  it('is NaN for a zone it does not know, rather than throwing', () => {
    expect(wallClockInstant({ date: '2026-09-28T09:00:00', timezone: 'Mars/Olympus' })).toBeNaN()
  })

  it('treats a missing zone as UTC', () => {
    const instant = wallClockInstant({ date: '2026-09-28T09:00:00', timezone: '' })
    expect(new Date(instant).toISOString()).toBe('2026-09-28T09:00:00.000Z')
  })
})

describe('compareWallClocks', () => {
  it('orders by instant, not by the reading', () => {
    const tokyo = { date: '2026-09-28T09:00:00', timezone: 'Asia/Tokyo' }
    const newYork = { date: '2026-09-28T08:00:00', timezone: 'America/New_York' }

    // The string comparison says the opposite, which is the whole reason this exists.
    expect(tokyo.date > newYork.date).toBe(true)
    expect(compareWallClocks(tokyo, newYork)).toBeLessThan(0)
  })

  it('sorts an unreadable row last rather than dropping it', () => {
    const good = { date: '2026-09-28T09:00:00', timezone: 'UTC' }
    const bad = { date: 'nonsense', timezone: 'UTC' }
    expect(compareWallClocks(bad, good)).toBeGreaterThan(0)
    expect(compareWallClocks(good, bad)).toBeLessThan(0)
    expect(compareWallClocks(bad, bad)).toBe(0)
  })
})

describe('wallClockIsPast', () => {
  it('is judged in the event zone, not the reader zone', () => {
    vi.useFakeTimers()
    // 20:00 UTC. An event at 19:00 in Tokyo (10:00 UTC) has happened; the same
    // reading in Los Angeles (2026-09-28T02:00Z next day) has not.
    vi.setSystemTime(new Date('2026-09-28T12:00:00Z'))

    expect(wallClockIsPast({ date: '2026-09-28T19:00:00', timezone: 'Asia/Tokyo' })).toBe(true)
    expect(wallClockIsPast({ date: '2026-09-28T19:00:00', timezone: 'America/Los_Angeles' })).toBe(false)
  })

  it('reads an unresolvable row as not past rather than hiding it', () => {
    expect(wallClockIsPast({ date: 'nonsense', timezone: 'UTC' })).toBe(false)
  })
})

describe('browserTimezone', () => {
  it('answers a real IANA name', () => {
    expect(wallClockInstant({ date: '2026-09-28T09:00:00', timezone: browserTimezone() })).not.toBeNaN()
  })
})
