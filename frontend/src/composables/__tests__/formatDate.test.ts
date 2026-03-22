import { describe, it, expect } from 'vitest'
import { formatDate } from '../formatDate'

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
