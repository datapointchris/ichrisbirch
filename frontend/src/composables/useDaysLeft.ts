export interface DaysLeftResult {
  text: string
  urgency: 'past' | 'two-weeks' | 'month' | 'none'
  totalDays: number
}

export function computeDaysLeft(dueDateString: string): DaysLeftResult {
  const date = new Date(dueDateString + 'T00:00:00')
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  const differenceMs = date.getTime() - today.getTime()

  if (differenceMs <= 0) {
    return { text: 'Past', urgency: 'past', totalDays: 0 }
  }

  let differenceDays = Math.floor(differenceMs / 86400000)
  const totalDays = differenceDays
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

export function formatDate(dateString: string): string {
  const date = new Date(dateString + 'T00:00:00')
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}
