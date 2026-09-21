import { describe, it, expect, afterEach, vi } from 'vitest'
import { zoneOptions } from '../zoneOptions'

const intl = Intl as typeof Intl & { supportedValuesOf: (key: 'timeZone') => string[] }

function browserKnows(zones: string[]) {
  vi.spyOn(intl, 'supportedValuesOf').mockReturnValue(zones)
}

function values(options: { value: string }[]): string[] {
  return options.map((o) => o.value)
}

describe('zoneOptions', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('lists UTC where the browser leaves it out', () => {
    browserKnows(['America/New_York', 'Europe/Paris'])
    expect(values(zoneOptions('America/New_York', 'America/New_York'))).toContain('UTC')
  })

  it('lists a selected zone the browser does not name, so the picker can show it', () => {
    browserKnows(['America/New_York', 'Europe/Paris'])
    expect(values(zoneOptions('America/New_York', 'US/Eastern'))).toContain('US/Eastern')
  })

  it('lists each zone once when own, selected and UTC coincide', () => {
    browserKnows(['UTC', 'Europe/Paris'])
    const listed = values(zoneOptions('UTC', 'UTC'))
    expect(listed.filter((tz) => tz === 'UTC')).toHaveLength(1)
  })

  it('marks the reader zone and no other', () => {
    browserKnows(['America/New_York', 'Europe/Paris'])
    const labels = zoneOptions('Europe/Paris', 'America/New_York', 'this browser').map((o) => o.label)
    expect(labels).toContain('Europe/Paris (this browser)')
    expect(labels.filter((label) => label.includes('(this browser)'))).toHaveLength(1)
  })
})
