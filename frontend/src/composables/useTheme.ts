import { watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { createLogger } from '@/utils/logger'

const logger = createLogger('Theme')

// --- Theme Colors (OKLCH hues) ---

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

export function getThemeHue(themeName: string): number | null {
  return themeHues[themeName] ?? null
}

export function applyTheme(themeName: string) {
  if (themeName === 'random') {
    const hue = Math.floor(Math.random() * 360)
    applyHue(hue)
    logger.info('theme_applied', { theme: 'random', hue })
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

// --- Font System ---

export interface FontDefinition {
  id: string
  name: string
  family: string
  category: 'monospace' | 'sans-serif'
  source: 'google' | 'self-hosted'
}

// Google Fonts are loaded via <link> tags injected into <head>
// Self-hosted fonts are loaded via @font-face in _fonts.scss
export const fonts: FontDefinition[] = [
  // Google Fonts — monospace
  { id: 'ubuntu-mono', name: 'Ubuntu Mono', family: '"Ubuntu Mono", monospace', category: 'monospace', source: 'google' },
  { id: 'fira-code', name: 'Fira Code', family: '"Fira Code", monospace', category: 'monospace', source: 'google' },
  { id: 'jetbrains-mono', name: 'JetBrains Mono', family: '"JetBrains Mono", monospace', category: 'monospace', source: 'google' },
  { id: 'roboto-mono', name: 'Roboto Mono', family: '"Roboto Mono", monospace', category: 'monospace', source: 'google' },
  // Google Fonts — proportional
  { id: 'inter', name: 'Inter', family: '"Inter", sans-serif', category: 'sans-serif', source: 'google' },
  { id: 'space-grotesk', name: 'Space Grotesk', family: '"Space Grotesk", sans-serif', category: 'sans-serif', source: 'google' },
  // Self-hosted — monospace
  { id: 'hack', name: 'Hack', family: '"Hack", monospace', category: 'monospace', source: 'self-hosted' },
  { id: 'commit-mono', name: 'Commit Mono', family: '"Commit Mono", monospace', category: 'monospace', source: 'self-hosted' },
  { id: 'comic-mono', name: 'Comic Mono', family: '"Comic Mono", monospace', category: 'monospace', source: 'self-hosted' },
  { id: 'iosevka', name: 'Iosevka', family: '"Iosevka", monospace', category: 'monospace', source: 'self-hosted' },
  { id: 'meslo', name: 'Meslo LG M', family: '"Meslo LG M", monospace', category: 'monospace', source: 'self-hosted' },
  { id: 'monaspace-neon', name: 'Monaspace Neon', family: '"Monaspace Neon", monospace', category: 'monospace', source: 'self-hosted' },
  { id: 'serious-shanns', name: 'Serious Shanns', family: '"Serious Shanns", monospace', category: 'monospace', source: 'self-hosted' },
  { id: 'comic-shanns', name: 'Comic Shanns', family: '"Comic Shanns", monospace', category: 'monospace', source: 'self-hosted' },
]

// Google Fonts API URLs keyed by font id
const googleFontUrls: Record<string, string> = {
  'ubuntu-mono': 'https://fonts.googleapis.com/css2?family=Ubuntu+Mono:wght@400;700&display=swap',
  'fira-code': 'https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;700&display=swap',
  'jetbrains-mono': 'https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap',
  'roboto-mono': 'https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap',
  inter: 'https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap',
  'space-grotesk': 'https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;700&display=swap',
}

// Track which Google Fonts have been loaded to avoid duplicate <link> tags
const loadedGoogleFonts = new Set<string>()

function loadGoogleFont(fontId: string) {
  if (loadedGoogleFonts.has(fontId)) return
  const url = googleFontUrls[fontId]
  if (!url) return

  const link = document.createElement('link')
  link.rel = 'stylesheet'
  link.href = url
  document.head.appendChild(link)
  loadedGoogleFonts.add(fontId)
}

export function applyFont(fontId: string) {
  const font = fonts.find((f) => f.id === fontId)
  if (!font) {
    logger.warning('font_unknown', { fontId })
    return
  }

  // Load Google Font stylesheet if needed
  if (font.source === 'google') {
    loadGoogleFont(font.id)
  }

  document.documentElement.style.setProperty('--ff-base', font.family)
  logger.info('font_applied', { fontId: font.id, family: font.family })
}

export function getFontById(fontId: string): FontDefinition | undefined {
  return fonts.find((f) => f.id === fontId)
}

// --- Combined Initialization ---

/**
 * Initialize theme color and font from user preferences and watch for changes.
 * Call once in App.vue.
 */
export function useTheme() {
  const auth = useAuthStore()

  watch(
    () => auth.preferences?.theme_color,
    (themeName) => {
      if (themeName) {
        applyTheme(themeName)
      }
    },
    { immediate: true }
  )

  watch(
    () => auth.preferences?.font_family,
    (fontId) => {
      if (fontId && typeof fontId === 'string') {
        applyFont(fontId)
      }
    },
    { immediate: true }
  )
}
