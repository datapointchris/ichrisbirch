/**
 * A calendar day travels as a `YYYY-MM-DD` key and is compared as one.
 *
 * Which day an instant falls on depends on a zone, so `dayKeyOf` takes one and
 * defaults to the user's. Everything after that is arithmetic on keys, done on
 * UTC midnights where no day is 23 or 25 hours long. `toISOString().slice(0, 10)`
 * on an instant is its UTC day and `getDate()` is the browser's, and neither is
 * the user's.
 *
 * A value with no offset is a reading rather than an instant — a stored day, or
 * a wall clock at a venue — so its day is the one written in it.
 */
import { displayZone } from './displayZone'

export type DayKey = string

const MS_PER_DAY = 86_400_000
const READING = /^\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?)?$/

const formatters = new Map<string, Intl.DateTimeFormat>()

function dayFormatter(zone: string): Intl.DateTimeFormat {
  let formatter = formatters.get(zone)
  if (!formatter) {
    formatter = new Intl.DateTimeFormat('en-US', { timeZone: zone, year: 'numeric', month: '2-digit', day: '2-digit' })
    formatters.set(zone, formatter)
  }
  return formatter
}

/** True for a value carrying no offset: a day, or a wall clock read as written. */
export function isReading(value: string): boolean {
  return READING.test(value)
}

/** The day `value` falls on in `zone`. */
export function dayKeyOf(value: string | number | Date, zone: string = displayZone()): DayKey {
  if (typeof value === 'string' && isReading(value)) return value.slice(0, 10)
  const instant = value instanceof Date ? value : new Date(value)
  const parts: Record<string, string> = {}
  for (const part of dayFormatter(zone).formatToParts(instant)) parts[part.type] = part.value
  return `${parts.year}-${parts.month}-${parts.day}`
}

export function todayKey(zone: string = displayZone(), now: number = Date.now()): DayKey {
  return dayKeyOf(now, zone)
}

function utcMidnight(key: DayKey): number {
  const [y, m, d] = key.split('-').map(Number)
  return Date.UTC(y!, m! - 1, d!)
}

function keyOfUtcMidnight(ms: number): DayKey {
  const date = new Date(ms)
  const month = String(date.getUTCMonth() + 1).padStart(2, '0')
  const day = String(date.getUTCDate()).padStart(2, '0')
  return `${date.getUTCFullYear()}-${month}-${day}`
}

/** True when `key` names a day that exists: `2026-02-31` does not. */
export function isCalendarDay(key: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(key) && keyOfUtcMidnight(utcMidnight(key)) === key
}

export function addDays(key: DayKey, days: number): DayKey {
  return keyOfUtcMidnight(utcMidnight(key) + days * MS_PER_DAY)
}

/**
 * Whole days from the day `from` falls on to the day `to` falls on, negative
 * when `to` is earlier. A task added at 23:00 and finished at 01:00 took a day.
 */
export function daysBetween(from: string, to: string, zone: string = displayZone()): number {
  return Math.round((utcMidnight(dayKeyOf(to, zone)) - utcMidnight(dayKeyOf(from, zone))) / MS_PER_DAY)
}

/** Whole days from the day `value` falls on to today. */
export function daysAgo(value: string, zone: string = displayZone()): number {
  return daysBetween(value, todayKey(zone), zone)
}

/** The Monday that opens the week `key` falls in. */
export function startOfWeek(key: DayKey): DayKey {
  const weekday = new Date(utcMidnight(key)).getUTCDay()
  return addDays(key, weekday === 0 ? -6 : 1 - weekday)
}

export function startOfMonth(key: DayKey): DayKey {
  return `${key.slice(0, 8)}01`
}

export function endOfMonth(key: DayKey): DayKey {
  const [y, m] = key.split('-').map(Number)
  return keyOfUtcMidnight(Date.UTC(y!, m!, 0))
}

/** The `YYYY-MM` month `value` falls in, in `zone`. */
export function monthKeyOf(value: string | number | Date, zone: string = displayZone()): string {
  return dayKeyOf(value, zone).slice(0, 7)
}
