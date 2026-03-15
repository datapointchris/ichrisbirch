import { describe, it, expect, beforeEach, vi } from 'vitest'
import { getThemeHue, applyTheme } from '../useTheme'

describe('applyTheme', () => {
  beforeEach(() => {
    // Reset --base-hue before each test
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
