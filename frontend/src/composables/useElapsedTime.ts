export interface ElapsedTimeResult {
  text: string
  totalDays: number
  years: number
  months: number
  days: number
  isOngoing: boolean
}

export function computeElapsedTime(startDateString: string, endDateString?: string): ElapsedTimeResult {
  const start = new Date(startDateString + 'T00:00:00')
  const end = endDateString ? new Date(endDateString + 'T00:00:00') : new Date()
  end.setHours(0, 0, 0, 0)

  const isOngoing = !endDateString
  const totalMs = end.getTime() - start.getTime()
  const totalDays = Math.max(0, Math.floor(totalMs / 86400000))

  // Calendar-accurate year/month/day breakdown
  let years = end.getFullYear() - start.getFullYear()
  let months = end.getMonth() - start.getMonth()
  let days = end.getDate() - start.getDate()

  if (days < 0) {
    months--
    // Days in the previous month
    const prevMonth = new Date(end.getFullYear(), end.getMonth(), 0)
    days += prevMonth.getDate()
  }
  if (months < 0) {
    years--
    months += 12
  }

  const parts: string[] = []
  if (years > 0) parts.push(years + (years > 1 ? ' years' : ' year'))
  if (months > 0) parts.push(months + (months > 1 ? ' months' : ' month'))
  if (days > 0) parts.push(days + (days > 1 ? ' days' : ' day'))

  const text = parts.length > 0 ? parts.join(', ') : 'Today'

  return { text, totalDays, years, months, days, isOngoing }
}

export function computeTimeBetween(date1String: string, date2String: string): ElapsedTimeResult {
  // Always compute from earlier to later date
  const d1 = new Date(date1String + 'T00:00:00')
  const d2 = new Date(date2String + 'T00:00:00')
  const [earlier, later] = d1 <= d2 ? [date1String, date2String] : [date2String, date1String]
  return computeElapsedTime(earlier, later)
}
