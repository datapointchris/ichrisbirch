import { daysBetween, todayKey, type DayKey } from './calendarDay'

export interface ElapsedTimeResult {
  text: string
  totalDays: number
  years: number
  months: number
  days: number
  isOngoing: boolean
}

function parts(key: DayKey): [number, number, number] {
  const [y, m, d] = key.split('-').map(Number)
  return [y!, m!, d!]
}

/** Calendar time from one day to another, or to today on the user's calendar. */
export function computeElapsedTime(startDateString: string, endDateString?: string): ElapsedTimeResult {
  const endKey = endDateString ?? todayKey()
  const isOngoing = !endDateString
  const totalDays = Math.max(0, daysBetween(startDateString, endKey))

  const [startYear, startMonth, startDay] = parts(startDateString)
  const [endYear, endMonth, endDay] = parts(endKey)
  let years = endYear - startYear
  let months = endMonth - startMonth
  let days = endDay - startDay

  if (days < 0) {
    months--
    // Day 0 of the end month is the last day of the month before it.
    days += new Date(Date.UTC(endYear, endMonth - 1, 0)).getUTCDate()
  }
  if (months < 0) {
    years--
    months += 12
  }

  const words: string[] = []
  if (years > 0) words.push(years + (years > 1 ? ' years' : ' year'))
  if (months > 0) words.push(months + (months > 1 ? ' months' : ' month'))
  if (days > 0) words.push(days + (days > 1 ? ' days' : ' day'))

  const text = words.length > 0 ? words.join(', ') : 'Today'

  return { text, totalDays, years, months, days, isOngoing }
}

export function computeTimeBetween(date1String: string, date2String: string): ElapsedTimeResult {
  const [earlier, later] = date1String <= date2String ? [date1String, date2String] : [date2String, date1String]
  return computeElapsedTime(earlier, later)
}
