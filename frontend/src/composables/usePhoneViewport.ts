import { onScopeDispose, ref, type Ref } from 'vue'

/**
 * Whether the viewport is a phone's, tracking rotation and resizes.
 *
 * The width comes from `--phone-max-width`, which the SCSS breakpoint publishes,
 * so script and styles switch at the same point. Where neither the property nor
 * `matchMedia` exists, as in a unit test, the answer is false.
 */
export function usePhoneViewport(): Ref<boolean> {
  const isPhone = ref(false)
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return isPhone

  const width = getComputedStyle(document.documentElement).getPropertyValue('--phone-max-width').trim()
  if (!width) return isPhone

  const query = window.matchMedia(`(max-width: ${width})`)
  isPhone.value = query.matches
  const update = (event: MediaQueryListEvent) => {
    isPhone.value = event.matches
  }
  query.addEventListener('change', update)
  onScopeDispose(() => query.removeEventListener('change', update))
  return isPhone
}
