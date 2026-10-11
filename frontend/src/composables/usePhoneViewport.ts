import { onScopeDispose, ref, type Ref } from 'vue'

/**
 * The query matching a phone's viewport, or null where it cannot be built.
 *
 * The width comes from `--phone-max-width`, which the SCSS breakpoint publishes,
 * so script and styles switch at the same point. Where neither the property nor
 * `matchMedia` exists, as in a unit test, there is no query.
 */
function phoneQuery(): MediaQueryList | null {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return null
  const width = getComputedStyle(document.documentElement).getPropertyValue('--phone-max-width').trim()
  return width ? window.matchMedia(`(max-width: ${width})`) : null
}

/** Whether the viewport is a phone's at this moment. */
export function isPhoneViewport(): boolean {
  return phoneQuery()?.matches ?? false
}

/** Whether the viewport is a phone's, tracking rotation and resizes. */
export function usePhoneViewport(): Ref<boolean> {
  const isPhone = ref(false)
  const query = phoneQuery()
  if (!query) return isPhone

  isPhone.value = query.matches
  const update = (event: MediaQueryListEvent) => {
    isPhone.value = event.matches
  }
  query.addEventListener('change', update)
  onScopeDispose(() => query.removeEventListener('change', update))
  return isPhone
}
