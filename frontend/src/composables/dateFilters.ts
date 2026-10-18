/**
 * The named windows the completed views filter by, as the instants the API takes.
 *
 * A window runs from its first day's first instant to the first instant after
 * its last day, both read in the display zone. That is the zone `todayKey`
 * reads today in, so "today" means the same day on the page and on the wire.
 */
import { addDays, dayStart, endOfMonth, startOfMonth, startOfWeek, todayKey, type DayKey } from './calendarDay'
import { displayZone } from './displayZone'

export type DateFilterKey = 'today' | 'yesterday' | 'this_week' | 'last_7' | 'this_month' | 'last_30' | 'this_year' | 'all'

export const DATE_FILTERS: DateFilterKey[] = ['today', 'yesterday', 'this_week', 'last_7', 'this_month', 'last_30', 'this_year', 'all']

/** The `since` and `until` query parameters of a read bounded by time. An absent end is open. */
export interface TimeWindow {
  since?: string
  until?: string
}

export function dateFilterLabel(key: DateFilterKey): string {
  return key
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

/** The window holding every day from `first` to `last`, both included. */
export function dayWindow(first: DayKey, last: DayKey = first, zone: string = displayZone()): TimeWindow {
  return { since: dayStart(first, zone), until: dayStart(addDays(last, 1), zone) }
}

export function dateFilterWindow(key: DateFilterKey, today: DayKey = todayKey(), zone: string = displayZone()): TimeWindow {
  switch (key) {
    case 'all':
      return {}
    case 'today':
      return dayWindow(today, today, zone)
    case 'yesterday':
      return dayWindow(addDays(today, -1), addDays(today, -1), zone)
    case 'this_week': {
      const monday = startOfWeek(today)
      return dayWindow(monday, addDays(monday, 6), zone)
    }
    case 'last_7':
      return dayWindow(addDays(today, -6), today, zone)
    case 'this_month':
      return dayWindow(startOfMonth(today), endOfMonth(today), zone)
    case 'last_30':
      return dayWindow(addDays(today, -29), today, zone)
    case 'this_year':
      return dayWindow(`${today.slice(0, 4)}-01-01`, `${today.slice(0, 4)}-12-31`, zone)
  }
}
