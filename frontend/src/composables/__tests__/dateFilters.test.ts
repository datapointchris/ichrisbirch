import { describe, it, expect } from 'vitest'
import { dateFilterRange } from '../dateFilters'

// Wednesday 23 September 2026.
const TODAY = '2026-09-23'

describe('dateFilterRange', () => {
  it('names each window as inclusive bare days, leaving the zone to the API', () => {
    expect(dateFilterRange('today', TODAY)).toEqual({ start: '2026-09-23', end: '2026-09-23' })
    expect(dateFilterRange('yesterday', TODAY)).toEqual({ start: '2026-09-22', end: '2026-09-22' })
    expect(dateFilterRange('this_week', TODAY)).toEqual({ start: '2026-09-21', end: '2026-09-27' })
    expect(dateFilterRange('last_7', TODAY)).toEqual({ start: '2026-09-16', end: '2026-09-23' })
    expect(dateFilterRange('this_month', TODAY)).toEqual({ start: '2026-09-01', end: '2026-09-30' })
    expect(dateFilterRange('last_30', TODAY)).toEqual({ start: '2026-08-24', end: '2026-09-23' })
    expect(dateFilterRange('this_year', TODAY)).toEqual({ start: '2026-01-01', end: '2026-12-31' })
  })

  it('leaves both bounds off for all', () => {
    expect(dateFilterRange('all', TODAY)).toEqual({})
  })

  it('opens a week on Monday when today is Sunday', () => {
    expect(dateFilterRange('this_week', '2026-09-27')).toEqual({ start: '2026-09-21', end: '2026-09-27' })
  })
})
