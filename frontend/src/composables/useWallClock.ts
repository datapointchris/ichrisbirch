/**
 * A wall clock and its zone are one value, and every reader has to resolve them
 * together before comparing against anything.
 *
 * `event.date` is a reading on a clock at the venue, with no offset. Read alone it
 * is whatever the reader's own zone makes of it: 09:00 in Tokyo and 08:00 in New
 * York sort as `['08:00', '09:00']` by string, and the Tokyo event is thirteen
 * hours earlier. Sorting, "is it past", and "how long until" are all that mistake.
 *
 * Rendering is the one operation that does not resolve. The number on the page is
 * the reading at the venue, so it is printed verbatim and the zone is named beside
 * it — converting it into the reader's zone would move the number and say nothing
 * about where the event is.
 */

/** A value carrying a wall clock and the IANA zone that resolves it. */
export interface WallClock {
  date: string
  timezone: string
}

/** The reader's own zone, resolved once so components do not each keep a copy. */
export function browserTimezone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'
}

/**
 * The instant a wall clock refers to, as epoch milliseconds.
 *
 * Uses the zone's own offset at that date, so an event on the far side of a DST
 * change resolves with the offset in force then rather than the one in force now.
 * An unreadable date or an unknown zone returns NaN, which sorts last and reads as
 * "not past" rather than taking the page down.
 */
export function wallClockInstant(value: WallClock): number {
  const parsed = parseWallClock(value.date)
  if (parsed === null) return Number.NaN

  const zone = value.timezone || 'UTC'
  try {
    // Read the naive components back out of the zone to learn its offset at that
    // date, then correct by the difference. Intl is the only thing in the browser
    // that knows a zone's historical and future offsets.
    const asUtc = Date.UTC(parsed.year, parsed.month - 1, parsed.day, parsed.hour, parsed.minute, parsed.second)
    const offset = zoneOffsetMs(asUtc, zone)
    return asUtc - offset
  } catch {
    return Number.NaN
  }
}

/** True when the event has already happened, in its own zone. */
export function wallClockIsPast(value: WallClock, now: number = Date.now()): boolean {
  const instant = wallClockInstant(value)
  return Number.isNaN(instant) ? false : instant < now
}

/** Compares two wall clocks as instants, for a sort. NaN sorts last. */
export function compareWallClocks(a: WallClock, b: WallClock): number {
  const left = wallClockInstant(a)
  const right = wallClockInstant(b)
  if (Number.isNaN(left)) return Number.isNaN(right) ? 0 : 1
  if (Number.isNaN(right)) return -1
  return left - right
}

interface WallClockParts {
  year: number
  month: number
  day: number
  hour: number
  minute: number
  second: number
}

/** Accepts `YYYY-MM-DDTHH:MM[:SS]` and a bare `YYYY-MM-DD`. Any offset is ignored. */
function parseWallClock(date: string): WallClockParts | null {
  const match = date.match(/^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2}))?)?/)
  if (!match) return null
  const [, year, month, day, hour, minute, second] = match
  return {
    year: Number(year),
    month: Number(month),
    day: Number(day),
    hour: Number(hour ?? 0),
    minute: Number(minute ?? 0),
    second: Number(second ?? 0),
  }
}

/** The zone's offset from UTC at a given instant, in milliseconds. */
function zoneOffsetMs(utcMs: number, zone: string): number {
  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZone: zone,
    hour12: false,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
  const parts: Record<string, number> = {}
  for (const part of formatter.formatToParts(new Date(utcMs))) {
    if (part.type !== 'literal') parts[part.type] = Number(part.value)
  }
  // Hour 24 appears at midnight under hour12: false in some engines.
  const hour = parts.hour === 24 ? 0 : (parts.hour ?? 0)
  const asZone = Date.UTC(parts.year!, parts.month! - 1, parts.day!, hour, parts.minute!, parts.second!)
  return asZone - utcMs
}
