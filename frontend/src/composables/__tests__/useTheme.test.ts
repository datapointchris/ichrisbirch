import { describe, it, expect, beforeEach, vi } from 'vitest'
import { getThemeHue, applyTheme, applyFont, getFontById, fonts, themes, getThemeById } from '../useTheme'

const NAMED_VARS = ['--clr-primary--darker', '--clr-primary', '--clr-primary--lighter', '--clr-text', '--clr-accent', '--clr-accent-light']

function clearAllThemeVars() {
  const el = document.documentElement
  el.style.removeProperty('--base-hue')
  for (const v of NAMED_VARS) {
    el.style.removeProperty(v)
  }
}

describe('applyTheme', () => {
  beforeEach(() => {
    clearAllThemeVars()
  })

  it('sets --base-hue for turquoise theme', () => {
    applyTheme('turquoise')
    expect(document.documentElement.style.getPropertyValue('--base-hue')).toBe('224')
  })

  it('sets --base-hue for blue theme', () => {
    applyTheme('blue')
    expect(document.documentElement.style.getPropertyValue('--base-hue')).toBe('260')
  })

  it('sets --base-hue for green theme', () => {
    applyTheme('green')
    expect(document.documentElement.style.getPropertyValue('--base-hue')).toBe('155')
  })

  it('sets --base-hue for red theme', () => {
    applyTheme('red')
    expect(document.documentElement.style.getPropertyValue('--base-hue')).toBe('27')
  })

  it('sets --base-hue for purple theme', () => {
    applyTheme('purple')
    expect(document.documentElement.style.getPropertyValue('--base-hue')).toBe('303')
  })

  it('sets a random hue for random theme', () => {
    vi.spyOn(Math, 'random').mockReturnValue(0.5)
    applyTheme('random')
    expect(document.documentElement.style.getPropertyValue('--base-hue')).toBe('180')
    vi.restoreAllMocks()
  })

  it('does not set hue for unknown theme', () => {
    applyTheme('nonexistent')
    expect(document.documentElement.style.getPropertyValue('--base-hue')).toBe('')
  })

  it('applies named theme by setting color CSS variables', () => {
    applyTheme('kanagawa')
    const el = document.documentElement
    expect(el.style.getPropertyValue('--clr-primary--darker')).toBe('#1f1f28')
    expect(el.style.getPropertyValue('--clr-primary')).toBe('#16161d')
    expect(el.style.getPropertyValue('--clr-text')).toBe('#dcd7ba')
    expect(el.style.getPropertyValue('--clr-accent')).toBe('#7e9cd8')
  })

  it('applies rose-pine named theme', () => {
    applyTheme('rose-pine')
    expect(document.documentElement.style.getPropertyValue('--clr-primary--darker')).toBe('#191724')
    expect(document.documentElement.style.getPropertyValue('--clr-accent')).toBe('#c4a7e7')
  })

  it('clears named theme overrides when switching to color theme', () => {
    applyTheme('kanagawa')
    expect(document.documentElement.style.getPropertyValue('--clr-primary--darker')).toBe('#1f1f28')
    applyTheme('turquoise')
    expect(document.documentElement.style.getPropertyValue('--clr-primary--darker')).toBe('')
    expect(document.documentElement.style.getPropertyValue('--base-hue')).toBe('224')
  })

  it('clears named theme overrides when switching to random', () => {
    vi.spyOn(Math, 'random').mockReturnValue(0.5)
    applyTheme('gruvbox')
    expect(document.documentElement.style.getPropertyValue('--clr-primary--darker')).toBe('#1d2021')
    applyTheme('random')
    expect(document.documentElement.style.getPropertyValue('--clr-primary--darker')).toBe('')
    vi.restoreAllMocks()
  })
})

describe('getThemeById', () => {
  it('returns theme definition for color theme', () => {
    const theme = getThemeById('turquoise')
    expect(theme).toBeDefined()
    expect(theme!.type).toBe('color')
    expect(theme!.hue).toBe(224)
  })

  it('returns theme definition for named theme', () => {
    const theme = getThemeById('kanagawa')
    expect(theme).toBeDefined()
    expect(theme!.type).toBe('named')
    expect(theme!.colors).toBeDefined()
  })

  it('returns undefined for unknown theme', () => {
    expect(getThemeById('nonexistent')).toBeUndefined()
  })
})

describe('themes list', () => {
  it('contains both color and named themes', () => {
    const color = themes.filter((t) => t.type === 'color')
    const named = themes.filter((t) => t.type === 'named')
    expect(color.length).toBeGreaterThan(0)
    expect(named.length).toBeGreaterThan(0)
  })

  it('has unique ids', () => {
    const ids = themes.map((t) => t.id)
    expect(new Set(ids).size).toBe(ids.length)
  })

  it('all named themes have colors defined', () => {
    const named = themes.filter((t) => t.type === 'named')
    for (const theme of named) {
      expect(theme.colors).toBeDefined()
      expect(theme.colors!.primaryDarker).toBeTruthy()
      expect(theme.colors!.accent).toBeTruthy()
    }
  })
})

describe('getThemeHue', () => {
  it('returns hue for known themes', () => {
    expect(getThemeHue('turquoise')).toBe(224)
    expect(getThemeHue('orange')).toBe(62)
    expect(getThemeHue('pink')).toBe(350)
  })

  it('returns null for unknown theme', () => {
    expect(getThemeHue('nonexistent')).toBeNull()
  })
})

describe('applyFont', () => {
  beforeEach(() => {
    document.documentElement.style.removeProperty('--ff-base')
  })

  it('sets --ff-base for a self-hosted font', () => {
    applyFont('hack')
    expect(document.documentElement.style.getPropertyValue('--ff-base')).toBe('"Hack", monospace')
  })

  it('sets --ff-base for a Google Font', () => {
    applyFont('fira-code')
    expect(document.documentElement.style.getPropertyValue('--ff-base')).toBe('"Fira Code", monospace')
  })

  it('sets --ff-base for a proportional font', () => {
    applyFont('inter')
    expect(document.documentElement.style.getPropertyValue('--ff-base')).toBe('"Inter", sans-serif')
  })

  it('does not set --ff-base for unknown font', () => {
    applyFont('nonexistent')
    expect(document.documentElement.style.getPropertyValue('--ff-base')).toBe('')
  })

  it('injects a <link> tag for Google Fonts', () => {
    const initialLinks = document.head.querySelectorAll('link[rel="stylesheet"]').length
    applyFont('jetbrains-mono')
    const newLinks = document.head.querySelectorAll('link[rel="stylesheet"]').length
    expect(newLinks).toBeGreaterThan(initialLinks)
  })

  it('does not inject a <link> tag for self-hosted fonts', () => {
    const initialLinks = document.head.querySelectorAll('link[rel="stylesheet"]').length
    applyFont('commit-mono')
    const newLinks = document.head.querySelectorAll('link[rel="stylesheet"]').length
    expect(newLinks).toBe(initialLinks)
  })
})

describe('getFontById', () => {
  it('returns font definition for known id', () => {
    const font = getFontById('hack')
    expect(font).toBeDefined()
    expect(font!.name).toBe('Hack')
    expect(font!.source).toBe('self-hosted')
  })

  it('returns undefined for unknown id', () => {
    expect(getFontById('nonexistent')).toBeUndefined()
  })
})

describe('fonts list', () => {
  it('contains both Google and self-hosted fonts', () => {
    const google = fonts.filter((f) => f.source === 'google')
    const selfHosted = fonts.filter((f) => f.source === 'self-hosted')
    expect(google.length).toBeGreaterThan(0)
    expect(selfHosted.length).toBeGreaterThan(0)
  })

  it('contains both monospace and sans-serif fonts', () => {
    const mono = fonts.filter((f) => f.category === 'monospace')
    const sans = fonts.filter((f) => f.category === 'sans-serif')
    expect(mono.length).toBeGreaterThan(0)
    expect(sans.length).toBeGreaterThan(0)
  })

  it('has unique ids', () => {
    const ids = fonts.map((f) => f.id)
    expect(new Set(ids).size).toBe(ids.length)
  })
})
