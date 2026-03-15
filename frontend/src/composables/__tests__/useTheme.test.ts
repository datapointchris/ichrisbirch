import { describe, it, expect, beforeEach, vi } from 'vitest'
import { getThemeHue, applyTheme, applyFont, getFontById, fonts } from '../useTheme'

describe('applyTheme', () => {
  beforeEach(() => {
    document.documentElement.style.removeProperty('--base-hue')
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
