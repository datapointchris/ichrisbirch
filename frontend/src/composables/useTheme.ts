import { watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { createLogger } from '@/utils/logger'

const logger = createLogger('Theme')

// OKLCH hue values for each theme name
// These produce perceptually uniform primary colors across all themes
const themeHues: Record<string, number> = {
  turquoise: 224,
  blue: 260,
  green: 155,
  orange: 62,
  red: 27,
  purple: 303,
  yellow: 104,
  pink: 350,
}

function applyHue(hue: number) {
  document.documentElement.style.setProperty('--base-hue', String(hue))
}

function applyRandomHue() {
  const hue = Math.floor(Math.random() * 360)
  applyHue(hue)
  logger.info('theme_applied', { theme: 'random', hue })
}

export function getThemeHue(themeName: string): number | null {
  return themeHues[themeName] ?? null
}

export function applyTheme(themeName: string) {
  if (themeName === 'random') {
    applyRandomHue()
    return
  }

  const hue = themeHues[themeName]
  if (hue !== undefined) {
    applyHue(hue)
    logger.info('theme_applied', { theme: themeName, hue })
  } else {
    logger.warning('theme_unknown', { theme: themeName })
  }
}

/**
 * Initialize theme from user preferences and watch for changes.
 * Call once in App.vue or main.ts.
 */
export function useTheme() {
  const auth = useAuthStore()

  // Apply theme whenever preferences change
  watch(
    () => auth.preferences?.theme_color,
    (themeName) => {
      if (themeName) {
        applyTheme(themeName)
      }
    },
    { immediate: true }
  )
}
