import { daysBetween, todayKey } from './calendarDay'

export interface DaysLeftResult {
  text: string
  urgency: 'past' | 'two-weeks' | 'month' | 'none'
  totalDays: number
}

/** Days from today to a due day, both read on the user's calendar. */
export function computeDaysLeft(dueDateString: string): DaysLeftResult {
  const totalDays = daysBetween(todayKey(), dueDateString)

  if (totalDays < 0) {
    return { text: 'Past', urgency: 'past', totalDays: 0 }
  }
  if (totalDays === 0) {
    return { text: 'Today', urgency: 'two-weeks', totalDays: 0 }
  }

  let differenceDays = totalDays
  const parts: string[] = []

  if (differenceDays > 365) {
    const years = Math.floor(differenceDays / 365)
    parts.push(years + (years > 1 ? ' years' : ' year'))
    differenceDays %= 365
  }

  if (differenceDays > 30) {
    const months = Math.floor(differenceDays / 30)
    parts.push(months + (months > 1 ? ' months' : ' month'))
    differenceDays %= 30
  }

  if (differenceDays >= 7) {
    const weeks = Math.floor(differenceDays / 7)
    parts.push(weeks + (weeks > 1 ? ' weeks' : ' week'))
    differenceDays %= 7
  }

  if (differenceDays > 0) {
    parts.push(differenceDays + (differenceDays > 1 ? ' days' : ' day'))
  }

  let urgency: DaysLeftResult['urgency'] = 'none'
  if (totalDays < 14) {
    urgency = 'two-weeks'
  } else if (totalDays < 30) {
    urgency = 'month'
  }

  return { text: parts.join(', '), totalDays, urgency }
}
