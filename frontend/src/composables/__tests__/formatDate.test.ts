import { describe, it, expect, vi, afterEach } from 'vitest'
import { formatDate, timeUntil } from '../formatDate'

const zone = vi.hoisted(() => ({ current: 'America/New_York' }))
vi.mock('../displayZone', () => ({ displayZone: () => zone.current }))

// 21:00 on 20 August in New York, which is already the 21st in UTC and Tokyo.
const NEW_YORK_EVENING = '2026-08-21T01:00:00Z'

afterEach(() => {
  zone.current = 'America/New_York'
  vi.useRealTimers()
})

describe('the zone a value is shown in', () => {
  it('shows an instant in the user zone', () => {
    expect(formatDate(NEW_YORK_EVENING, 'shortDate')).toBe('Aug 20, 2026')
    expect(formatDate(NEW_YORK_EVENING, 'timestamp')).toMatch(/^2026-08-20, 9:00:00\s*PM$/)
  })

  it('follows the preference rather than the browser', () => {
    zone.current = 'Asia/Tokyo'
    expect(formatDate(NEW_YORK_EVENING, 'shortDate')).toBe('Aug 21, 2026')
  })

  it('prints a stored day as written in any zone', () => {
    zone.current = 'Pacific/Honolulu'
    expect(formatDate('2026-08-20', 'shortDate')).toBe('Aug 20, 2026')
  })

  it('prints a wall clock with no offset as written in any zone', () => {
    zone.current = 'Asia/Tokyo'
    expect(formatDate('2026-03-21T19:00:00', 'weekdayDateTime')).toMatch(/Saturday, Mar 21, 2026.*7:00\s*PM/)
  })
})

describe('timeUntil', () => {
  it('counts calendar days in the user zone, not elapsed hours', () => {
    // 23:00 in New York; an instant two hours later is tomorrow there.
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-08-21T03:00:00Z'))
    expect(timeUntil('2026-08-21T05:00:00Z')).toBe('tomorrow')
    expect(timeUntil('2026-08-20')).toBe('today')
    expect(timeUntil('2026-08-18')).toBe('2 days ago')
  })

  it('returns an empty string for no date', () => {
    expect(timeUntil(null)).toBe('')
  })
})

describe('formatDate', () => {
  describe('shortDate', () => {
    it('formats date-only string', () => {
      expect(formatDate('2026-12-25', 'shortDate')).toBe('Dec 25, 2026')
    })

    it('formats datetime string', () => {
      expect(formatDate('2026-03-05T14:30:00Z', 'shortDate')).toMatch(/Mar \d+, 2026/)
    })

    it('formats single-digit day without padding', () => {
      expect(formatDate('2026-03-05', 'shortDate')).toBe('Mar 5, 2026')
    })
  })

  describe('dateTime', () => {
    it('includes time without seconds', () => {
      const result = formatDate('2026-06-15T14:30:00', 'dateTime')
      expect(result).toContain('Jun')
      expect(result).toContain('2026')
      expect(result).toMatch(/2:30\s*PM/)
    })
  })

  describe('timestamp', () => {
    it('formats with yyyy-mm-dd date part', () => {
      const result = formatDate('2026-06-15T14:30:45', 'timestamp')
      expect(result).toMatch(/^2026-06-15,/)
      expect(result).toMatch(/2:30:45\s*PM/)
    })

    it('zero-pads month and day', () => {
      const result = formatDate('2026-03-05T09:05:03', 'timestamp')
      expect(result).toMatch(/^2026-03-05,/)
    })
  })

  describe('weekdayDate', () => {
    it('includes full weekday name and short month', () => {
      const result = formatDate('2026-03-21', 'weekdayDate')
      expect(result).toContain('Saturday')
      expect(result).toContain('Mar')
      expect(result).toContain('2026')
    })
  })

  describe('weekdayDateTime', () => {
    it('includes weekday and time', () => {
      const result = formatDate('2026-03-21T19:00:00', 'weekdayDateTime')
      expect(result).toContain('Saturday')
      expect(result).toContain('Mar')
      expect(result).toMatch(/7:00\s*PM/)
    })
  })

  describe('monthDay', () => {
    it('shows only month and day', () => {
      expect(formatDate('2026-12-25', 'monthDay')).toBe('Dec 25')
    })
  })

  describe('null/undefined handling', () => {
    it('returns N/A for null', () => {
      expect(formatDate(null, 'shortDate')).toBe('N/A')
    })

    it('returns N/A for undefined', () => {
      expect(formatDate(undefined, 'shortDate')).toBe('N/A')
    })

    it('returns N/A for empty string', () => {
      expect(formatDate('', 'shortDate')).toBe('N/A')
    })
  })
})
