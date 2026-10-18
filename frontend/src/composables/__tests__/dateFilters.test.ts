import { describe, it, expect } from 'vitest'
import { dateFilterWindow } from '../dateFilters'

// Wednesday 23 September 2026.
const TODAY = '2026-09-23'
const NEW_YORK = 'America/New_York'

describe('dateFilterWindow', () => {
  it('runs from the first day opening to the day after the last opening, in the zone', () => {
    expect(dateFilterWindow('today', TODAY, NEW_YORK)).toEqual({ since: '2026-09-23T04:00:00.000Z', until: '2026-09-24T04:00:00.000Z' })
    expect(dateFilterWindow('yesterday', TODAY, NEW_YORK)).toEqual({ since: '2026-09-22T04:00:00.000Z', until: '2026-09-23T04:00:00.000Z' })
    expect(dateFilterWindow('this_week', TODAY, NEW_YORK)).toEqual({ since: '2026-09-21T04:00:00.000Z', until: '2026-09-28T04:00:00.000Z' })
    expect(dateFilterWindow('last_7', TODAY, NEW_YORK)).toEqual({ since: '2026-09-17T04:00:00.000Z', until: '2026-09-24T04:00:00.000Z' })
    expect(dateFilterWindow('this_month', TODAY, NEW_YORK)).toEqual({
      since: '2026-09-01T04:00:00.000Z',
      until: '2026-10-01T04:00:00.000Z',
    })
    expect(dateFilterWindow('last_30', TODAY, NEW_YORK)).toEqual({ since: '2026-08-25T04:00:00.000Z', until: '2026-09-24T04:00:00.000Z' })
    expect(dateFilterWindow('this_year', TODAY, NEW_YORK)).toEqual({ since: '2026-01-01T05:00:00.000Z', until: '2027-01-01T05:00:00.000Z' })
  })

  it('leaves both ends open for all', () => {
    expect(dateFilterWindow('all', TODAY, NEW_YORK)).toEqual({})
  })

  it('opens a week on Monday when today is Sunday', () => {
    expect(dateFilterWindow('this_week', '2026-09-27', NEW_YORK).since).toBe('2026-09-21T04:00:00.000Z')
  })

  it('opens a day at its own midnight on the day a zone east of UTC changes offset', () => {
    // Sydney leaves daylight time at 03:00 on 5 April 2026, so midnight is still +11.
    expect(dateFilterWindow('today', '2026-04-05', 'Australia/Sydney')).toEqual({
      since: '2026-04-04T13:00:00.000Z',
      until: '2026-04-05T14:00:00.000Z',
    })
  })
})
