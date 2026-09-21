import { dayKeyOf, daysBetween, todayKey } from './calendarDay'
import { displayZone } from './displayZone'

export type DateFormat = 'shortDate' | 'dateTime' | 'timestamp' | 'weekdayDate' | 'weekdayDateTime' | 'monthDay'

const OPTIONS: Record<Exclude<DateFormat, 'timestamp'> | 'timeWithSeconds', Intl.DateTimeFormatOptions> = {
  shortDate: { year: 'numeric', month: 'short', day: 'numeric' },
  dateTime: { year: 'numeric', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' },
  weekdayDate: { weekday: 'long', year: 'numeric', month: 'short', day: 'numeric' },
  weekdayDateTime: { weekday: 'long', year: 'numeric', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' },
  monthDay: { month: 'short', day: 'numeric' },
  timeWithSeconds: { hour: 'numeric', minute: '2-digit', second: '2-digit' },
}

const formatters = new Map<string, Intl.DateTimeFormat>()

function formatterFor(name: keyof typeof OPTIONS, zone: string): Intl.DateTimeFormat {
  const key = `${name}|${zone}`
  let formatter = formatters.get(key)
  if (!formatter) {
    formatter = new Intl.DateTimeFormat('en-US', { ...OPTIONS[name], timeZone: zone })
    formatters.set(key, formatter)
  }
  return formatter
}

const READING_PARTS = /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2})(?:\.\d+)?)?)?$/

// A value with no offset is a reading, a stored day or a wall clock at a venue,
// and is printed as written: its parts are placed on a UTC clock and read back in
// UTC. A value with an offset is an instant, shown in the user's zone.
function resolve(value: string): { date: Date; zone: string } {
  const reading = value.match(READING_PARTS)
  if (reading) {
    const [, y, mo, d, h, mi, s] = reading.map(Number)
    return { date: new Date(Date.UTC(y!, mo! - 1, d!, h || 0, mi || 0, s || 0)), zone: 'UTC' }
  }
  return { date: new Date(value), zone: displayZone() }
}

/** Calendar days from today to the day `dateString` falls on, in words. */
export function timeUntil(dateString: string | null | undefined): string {
  if (!dateString) return ''
  const diffDays = daysBetween(todayKey(), dayKeyOf(dateString))

  if (diffDays === 0) return 'today'
  if (diffDays === 1) return 'tomorrow'
  if (diffDays === -1) return 'yesterday'
  if (diffDays > 0) return `in ${diffDays} days`
  return `${Math.abs(diffDays)} days ago`
}

export function formatDate(dateString: string | null | undefined, format: DateFormat): string {
  if (!dateString) return 'N/A'
  const { date, zone } = resolve(dateString)

  if (format === 'timestamp') {
    return `${dayKeyOf(date, zone)}, ${formatterFor('timeWithSeconds', zone).format(date)}`
  }

  return formatterFor(format, zone).format(date)
}
