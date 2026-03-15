import { watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { createLogger } from '@/utils/logger'

const logger = createLogger('Theme')

// --- Theme System ---

export interface ThemeDefinition {
  id: string
  name: string
  type: 'color' | 'named'
  // For 'color' themes: OKLCH hue rotation
  hue?: number
  // For 'named' themes: specific color overrides from theme.yml
  colors?: {
    primaryDarker: string
    primary: string
    primaryLighter: string
    text: string
    accent: string
    accentLight: string
  }
  // Preview swatch color for the selector
  swatch: string
}

// CSS variables that named themes override (cleared when switching away)
const NAMED_THEME_VARS = [
  '--clr-primary--darker',
  '--clr-primary',
  '--clr-primary--lighter',
  '--clr-text',
  '--clr-accent',
  '--clr-accent-light',
] as const

// CSS variables for custom accent/tertiary hues (cleared when switching to named themes)
const CUSTOM_HUE_VARS = ['--accent-hue'] as const

export const themes: ThemeDefinition[] = [
  // Simple color themes — OKLCH hue rotation
  { id: 'turquoise', name: 'Turquoise', type: 'color', hue: 224, swatch: '#00363f' },
  { id: 'blue', name: 'Blue', type: 'color', hue: 260, swatch: '#17263e' },
  { id: 'green', name: 'Green', type: 'color', hue: 155, swatch: '#0e2d1b' },
  { id: 'orange', name: 'Orange', type: 'color', hue: 62, swatch: '#372009' },
  { id: 'red', name: 'Red', type: 'color', hue: 27, swatch: '#3b1b18' },
  { id: 'purple', name: 'Purple', type: 'color', hue: 303, swatch: '#2b1f3a' },
  { id: 'yellow', name: 'Yellow', type: 'color', hue: 104, swatch: '#2a2705' },
  { id: 'pink', name: 'Pink', type: 'color', hue: 350, swatch: '#381b29' },
  { id: 'random', name: 'Random', type: 'color', swatch: 'linear-gradient(135deg, #e74c3c, #f1c40f, #27ae60, #2980b9, #8e44ad)' },

  // Named themes — bespoke palettes from theme.yml
  {
    id: 'charcoal-ember',
    name: 'Charcoal Ember',
    type: 'named',
    swatch: '#1d1f21',
    colors: {
      primaryDarker: '#1d1f21',
      primary: '#2d2d2d',
      primaryLighter: '#373b41',
      text: '#c5c8c6',
      accent: '#4eb6fe',
      accentLight: '#ffc400',
    },
  },
  {
    id: 'kanagawa',
    name: 'Kanagawa',
    type: 'named',
    swatch: '#1f1f28',
    colors: {
      primaryDarker: '#1f1f28',
      primary: '#16161d',
      primaryLighter: '#2a2a37',
      text: '#dcd7ba',
      accent: '#7e9cd8',
      accentLight: '#e6c384',
    },
  },
  {
    id: 'rose-pine',
    name: 'Rose Pine',
    type: 'named',
    swatch: '#191724',
    colors: {
      primaryDarker: '#191724',
      primary: '#1f1d2e',
      primaryLighter: '#26233a',
      text: '#e0def4',
      accent: '#c4a7e7',
      accentLight: '#ebbcba',
    },
  },
  {
    id: 'gruvbox',
    name: 'Gruvbox',
    type: 'named',
    swatch: '#1d2021',
    colors: {
      primaryDarker: '#1d2021',
      primary: '#282828',
      primaryLighter: '#3c3836',
      text: '#ebdbb2',
      accent: '#83a598',
      accentLight: '#fabd2f',
    },
  },
  {
    id: 'nord',
    name: 'Nordic',
    type: 'named',
    swatch: '#242933',
    colors: {
      primaryDarker: '#242933',
      primary: '#191d24',
      primaryLighter: '#2e3440',
      text: '#bbc3d4',
      accent: '#88c0d0',
      accentLight: '#ebcb8b',
    },
  },
  {
    id: 'nightfox',
    name: 'Nightfox',
    type: 'named',
    swatch: '#192330',
    colors: {
      primaryDarker: '#192330',
      primary: '#131a24',
      primaryLighter: '#212e3f',
      text: '#cdcecf',
      accent: '#719cd6',
      accentLight: '#dbc074',
    },
  },
  {
    id: 'everforest',
    name: 'Everforest',
    type: 'named',
    swatch: '#1e2326',
    colors: {
      primaryDarker: '#1e2326',
      primary: '#272e33',
      primaryLighter: '#2e383c',
      text: '#d3c6aa',
      accent: '#a7c080',
      accentLight: '#dbbc7f',
    },
  },
  {
    id: 'solarized-osaka',
    name: 'Solarized Osaka',
    type: 'named',
    swatch: '#001419',
    colors: {
      primaryDarker: '#001419',
      primary: '#001419',
      primaryLighter: '#002b36',
      text: '#93a1a1',
      accent: '#268bd2',
      accentLight: '#b58900',
    },
  },
  {
    id: 'terafox',
    name: 'Terafox',
    type: 'named',
    swatch: '#152528',
    colors: {
      primaryDarker: '#152528',
      primary: '#0f1c1e',
      primaryLighter: '#1d3337',
      text: '#e6eaea',
      accent: '#5a93aa',
      accentLight: '#ead49b',
    },
  },
  {
    id: 'oceanic-next',
    name: 'Oceanic Next',
    type: 'named',
    swatch: '#162c35',
    colors: {
      primaryDarker: '#162c35',
      primary: '#1b2b34',
      primaryLighter: '#343d46',
      text: '#c0c5ce',
      accent: '#6699cc',
      accentLight: '#fac863',
    },
  },
  {
    id: 'flexoki',
    name: 'Flexoki Moon',
    type: 'named',
    swatch: '#100f0f',
    colors: {
      primaryDarker: '#100f0f',
      primary: '#1c1b1a',
      primaryLighter: '#282726',
      text: '#cecdc3',
      accent: '#3aa99f',
      accentLight: '#d0a215',
    },
  },
  {
    id: 'retrobox',
    name: 'Retrobox',
    type: 'named',
    swatch: '#1c1c1c',
    colors: {
      primaryDarker: '#1c1c1c',
      primary: '#282828',
      primaryLighter: '#3c3836',
      text: '#ebdbb2',
      accent: '#83a598',
      accentLight: '#fabd2f',
    },
  },
]

function clearNamedThemeOverrides() {
  const el = document.documentElement
  for (const prop of NAMED_THEME_VARS) {
    el.style.removeProperty(prop)
  }
}

function clearCustomHueOverrides() {
  const el = document.documentElement
  for (const prop of CUSTOM_HUE_VARS) {
    el.style.removeProperty(prop)
  }
}

export function applyTheme(themeName: string) {
  // Random picks from ALL themes — color hues and named palettes
  if (themeName === 'random') {
    const nonRandomThemes = themes.filter((t) => t.id !== 'random')
    const pick = nonRandomThemes[Math.floor(Math.random() * nonRandomThemes.length)]
    if (!pick) return
    applyTheme(pick.id)
    logger.info('random_theme_picked', { picked: pick.id })
    return
  }

  const theme = themes.find((t) => t.id === themeName)
  if (!theme) {
    logger.warning('theme_unknown', { theme: themeName })
    return
  }

  if (theme.type === 'color' && theme.hue !== undefined) {
    clearNamedThemeOverrides()
    document.documentElement.style.setProperty('--base-hue', String(theme.hue))
    logger.info('theme_applied', { theme: theme.id, type: 'color', hue: theme.hue })
  } else if (theme.type === 'named' && theme.colors) {
    clearCustomHueOverrides()
    const el = document.documentElement
    el.style.setProperty('--clr-primary--darker', theme.colors.primaryDarker)
    el.style.setProperty('--clr-primary', theme.colors.primary)
    el.style.setProperty('--clr-primary--lighter', theme.colors.primaryLighter)
    el.style.setProperty('--clr-text', theme.colors.text)
    el.style.setProperty('--clr-accent', theme.colors.accent)
    el.style.setProperty('--clr-accent-light', theme.colors.accentLight)
    logger.info('theme_applied', { theme: theme.id, type: 'named' })
  }
}

/**
 * Apply a custom accent hue. Only works with color themes (not named themes).
 */
export function applyAccentHue(hue: number) {
  document.documentElement.style.setProperty('--accent-hue', String(hue))
  logger.info('accent_hue_applied', { hue })
}

export function getThemeById(themeId: string): ThemeDefinition | undefined {
  return themes.find((t) => t.id === themeId)
}

// Legacy helper for tests
export function getThemeHue(themeName: string): number | null {
  const theme = themes.find((t) => t.id === themeName)
  return theme?.hue ?? null
}

// --- Font System ---

export interface FontDefinition {
  id: string
  name: string
  family: string
  category: 'monospace' | 'sans-serif'
  source: 'google' | 'self-hosted'
}

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
  { id: 'commit-mono', name: 'Commit Mono', family: '"CommitMono", monospace', category: 'monospace', source: 'self-hosted' },
  { id: 'comic-mono', name: 'Comic Mono', family: '"Comic Mono", monospace', category: 'monospace', source: 'self-hosted' },
  { id: 'iosevka', name: 'Iosevka', family: '"Iosevka", monospace', category: 'monospace', source: 'self-hosted' },
  { id: 'meslo', name: 'Meslo LG M', family: '"Meslo LG M", monospace', category: 'monospace', source: 'self-hosted' },
  { id: 'monaspace-neon', name: 'Monaspace Neon', family: '"Monaspace Neon", monospace', category: 'monospace', source: 'self-hosted' },
  { id: 'serious-shanns', name: 'Serious Shanns', family: '"Serious Shanns", monospace', category: 'monospace', source: 'self-hosted' },
  { id: 'comic-shanns', name: 'Comic Shanns', family: '"Comic Shanns", monospace', category: 'monospace', source: 'self-hosted' },
]

const googleFontUrls: Record<string, string> = {
  'ubuntu-mono': 'https://fonts.googleapis.com/css2?family=Ubuntu+Mono:wght@400;700&display=swap',
  'fira-code': 'https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;700&display=swap',
  'jetbrains-mono': 'https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap',
  'roboto-mono': 'https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap',
  inter: 'https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap',
  'space-grotesk': 'https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;700&display=swap',
}

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

  // Apply custom accent hue (only for color themes, not named)
  watch(
    () => auth.preferences?.custom_accent_hue,
    (hue) => {
      if (typeof hue === 'number') {
        const currentTheme = themes.find((t) => t.id === auth.preferences?.theme_color)
        if (currentTheme?.type === 'color') {
          applyAccentHue(hue)
        }
      }
    },
    { immediate: true }
  )
}
