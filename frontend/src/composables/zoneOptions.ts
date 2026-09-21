import type { NeuSelectOption } from '@/components/NeuSelect.vue'

// supportedValuesOf is ES2022 and not in the lib target, so it is read off a narrowed
// view of Intl rather than by widening the global. Where it is missing there is still
// a usable list — the reader's own zone and UTC cover the cases that are not travel.
const intlWithZones = Intl as typeof Intl & { supportedValuesOf?: (key: 'timeZone') => string[] }

/** Every IANA zone the browser knows, with `own` always listed and marked. */
export function zoneOptions(own: string, mark = 'yours'): NeuSelectOption<string>[] {
  const names = intlWithZones.supportedValuesOf?.('timeZone') ?? [own, 'UTC']
  const all = names.includes(own) ? names : [own, ...names]
  return all.map((tz) => ({ value: tz, label: tz === own ? `${tz} (${mark})` : tz }))
}
