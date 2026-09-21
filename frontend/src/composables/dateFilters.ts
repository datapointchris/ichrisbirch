/**
 * The named windows the completed views filter by, as inclusive bare days.
 *
 * The API reads a bare day in the user's `timezone` preference, which is also
 * the zone `todayKey` reads today in. So a window goes out as days and is never
 * converted to instants here. The API widens the end day to the start of the
 * next one itself.
 */
import { addDays, endOfMonth, startOfMonth, startOfWeek, todayKey, type DayKey } from './calendarDay'

export type DateFilterKey = 'today' | 'yesterday' | 'this_week' | 'last_7' | 'this_month' | 'last_30' | 'this_year' | 'all'

export const DATE_FILTERS: DateFilterKey[] = ['today', 'yesterday', 'this_week', 'last_7', 'this_month', 'last_30', 'this_year', 'all']

export interface DayRange {
  start?: DayKey
  end?: DayKey
}

export function dateFilterLabel(key: DateFilterKey): string {
  return key
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

export function dateFilterRange(key: DateFilterKey, today: DayKey = todayKey()): DayRange {
  switch (key) {
    case 'all':
      return {}
    case 'today':
      return { start: today, end: today }
    case 'yesterday': {
      const yesterday = addDays(today, -1)
      return { start: yesterday, end: yesterday }
    }
    case 'this_week': {
      const monday = startOfWeek(today)
      return { start: monday, end: addDays(monday, 6) }
    }
    case 'last_7':
      return { start: addDays(today, -7), end: today }
    case 'this_month':
      return { start: startOfMonth(today), end: endOfMonth(today) }
    case 'last_30':
      return { start: addDays(today, -30), end: today }
    case 'this_year':
      return { start: `${today.slice(0, 4)}-01-01`, end: `${today.slice(0, 4)}-12-31` }
  }
}
