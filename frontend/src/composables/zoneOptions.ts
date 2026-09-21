import type { NeuSelectOption } from '@/components/NeuSelect.vue'

// supportedValuesOf is ES2022 and not in the lib target, so it is read off a narrowed
// view of Intl rather than by widening the global.
const intlWithZones = Intl as typeof Intl & { supportedValuesOf?: (key: 'timeZone') => string[] }

/**
 * Every IANA zone the browser knows, with `own` marked.
 *
 * `own`, `selected` and UTC are always listed. The browser answers canonical names
 * only, and some engines leave UTC out, so a stored zone could otherwise be missing
 * and the picker would show nothing selected.
 */
export function zoneOptions(own: string, selected: string, mark = 'yours'): NeuSelectOption<string>[] {
  const known = intlWithZones.supportedValuesOf?.('timeZone') ?? []
  const missing = [own, selected, 'UTC'].filter((tz) => tz && !known.includes(tz))
  return [...new Set([...missing, ...known])].map((tz) => ({ value: tz, label: tz === own ? `${tz} (${mark})` : tz }))
}
