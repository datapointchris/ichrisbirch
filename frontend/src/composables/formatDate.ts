export type DateFormat = 'shortDate' | 'dateTime' | 'timestamp' | 'weekdayDate' | 'weekdayDateTime' | 'monthDay'

const formatters: Record<Exclude<DateFormat, 'timestamp'>, Intl.DateTimeFormat> = {
  shortDate: new Intl.DateTimeFormat('en-US', { year: 'numeric', month: 'short', day: 'numeric' }),
  dateTime: new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }),
  weekdayDate: new Intl.DateTimeFormat('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }),
  weekdayDateTime: new Intl.DateTimeFormat('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }),
  monthDay: new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }),
}

const timeWithSeconds = new Intl.DateTimeFormat('en-US', {
  hour: 'numeric',
  minute: '2-digit',
  second: '2-digit',
})

export function formatDate(dateString: string | null | undefined, format: DateFormat): string {
  if (!dateString) return 'N/A'
  // Date-only strings (YYYY-MM-DD) parse as UTC midnight, shifting back a day in local time.
  // Appending T00:00:00 forces local-time parsing.
  const normalized = /^\d{4}-\d{2}-\d{2}$/.test(dateString) ? dateString + 'T00:00:00' : dateString
  const date = new Date(normalized)

  if (format === 'timestamp') {
    const y = date.getFullYear()
    const m = String(date.getMonth() + 1).padStart(2, '0')
    const d = String(date.getDate()).padStart(2, '0')
    return `${y}-${m}-${d}, ${timeWithSeconds.format(date)}`
  }

  return formatters[format].format(date)
}
