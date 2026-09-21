/**
 * The zone every instant on the page is shown in, and every "today" is read in.
 *
 * It is the user's `timezone` preference. The API reads a bare day in the same
 * preference, so a day the page asks for is the day the server answers with, on
 * whatever machine the page is open. Before the signed-in user loads, it is the
 * browser's zone.
 */
import { ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { createLogger } from '@/utils/logger'
import { browserTimezone } from './useWallClock'

const logger = createLogger('DisplayZone')

const zone = ref(browserTimezone())

/** Reactive: a template calling this re-renders when the preference changes. */
export function displayZone(): string {
  return zone.value
}

/** Follows the preference, and records the browser's zone for a user who has none. */
export function useDisplayZone() {
  const auth = useAuthStore()

  watch(
    () => auth.user,
    (user) => {
      if (!user) return
      const chosen = user.preferences?.timezone
      if (typeof chosen === 'string' && chosen) {
        zone.value = chosen
        return
      }
      const detected = browserTimezone()
      zone.value = detected
      auth.updatePreferences({ timezone: detected }).catch(() => {
        logger.warning('timezone_preference_not_recorded', { zone: detected })
      })
    },
    { immediate: true }
  )
}
