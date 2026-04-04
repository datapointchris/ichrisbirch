/**
 * Shared chart theming and option builders for stats pages.
 * Reads colors from the active theme's CSS custom properties so charts
 * adapt to named themes, accent hue slider, and dark/light backgrounds.
 */

import { Chart as ChartJS, BarElement, CategoryScale, LinearScale, Title, Tooltip, Legend } from 'chart.js'

ChartJS.register(BarElement, CategoryScale, LinearScale, Title, Tooltip, Legend)

// --- Shared stats computation utilities ---

/** Group items by year-month and count them. Returns sorted by month ascending. */
export function countByMonth<T>(items: T[], getDate: (item: T) => string | undefined): { month: string; count: number }[] {
  const counts = new Map<string, number>()
  for (const item of items) {
    const dateStr = getDate(item)
    if (!dateStr) continue
    const month = dateStr.slice(0, 7)
    counts.set(month, (counts.get(month) ?? 0) + 1)
  }
  return [...counts.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([month, count]) => ({ month, count }))
}

/** Group items by a derived label and count occurrences. Returns sorted by count descending. */
export function countByLabel<T>(items: T[], getLabel: (item: T) => string): { label: string; count: number }[] {
  const counts = new Map<string, number>()
  for (const item of items) {
    const label = getLabel(item)
    counts.set(label, (counts.get(label) ?? 0) + 1)
  }
  return [...counts.entries()].sort(([, a], [, b]) => b - a).map(([label, count]) => ({ label, count }))
}

/** Average of a numeric array, rounded to 1 decimal. Returns 0 for empty input. */
export function average(values: number[]): number {
  if (values.length === 0) return 0
  return Math.round((values.reduce((sum, v) => sum + v, 0) / values.length) * 10) / 10
}

/** Days between two date strings. */
export function daysBetween(start: string, end: string): number {
  return Math.floor((new Date(end).getTime() - new Date(start).getTime()) / (1000 * 60 * 60 * 24))
}

/** Days from a date string to today. */
export function daysAgo(dateStr: string): number {
  return Math.floor((Date.now() - new Date(dateStr).getTime()) / (1000 * 60 * 60 * 24))
}

// --- Chart theming ---

// Fallbacks for SSR / testing where document isn't available
const FALLBACK_TEXT = 'hsl(0 0% 85%)'
const FALLBACK_GRID = 'hsl(0 0% 27%)'

/** Read a CSS custom property's current computed value. */
function cssVar(name: string, fallback: string): string {
  if (typeof document === 'undefined') return fallback
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback
}

/**
 * Add alpha transparency to a resolved CSS color string.
 * Handles rgb(), rgba(), oklch(), hsl(), and hex formats.
 */
function withAlpha(color: string, alpha: number): string {
  // rgb(r, g, b) or rgb(r g b)
  const rgbMatch = color.match(/^rgb\(([^)]+)\)$/)
  if (rgbMatch) return `rgba(${rgbMatch[1]}, ${alpha})`

  // rgba — replace existing alpha
  const rgbaMatch = color.match(/^rgba\((.+),\s*[\d.]+\)$/)
  if (rgbaMatch) return `rgba(${rgbaMatch[1]}, ${alpha})`

  // oklch(L C H) → oklch(L C H / alpha)
  const oklchMatch = color.match(/^oklch\(([^/)]+)\)$/)
  if (oklchMatch?.[1]) return `oklch(${oklchMatch[1].trim()} / ${alpha})`

  // oklch with existing alpha — replace it
  const oklchAlphaMatch = color.match(/^oklch\((.+?)\s*\/\s*[\d.]+\)$/)
  if (oklchAlphaMatch?.[1]) return `oklch(${oklchAlphaMatch[1].trim()} / ${alpha})`

  // hsl(h, s%, l%) → hsla(h, s%, l%, alpha)
  const hslMatch = color.match(/^hsl\(([^)]+)\)$/)
  if (hslMatch) return `hsla(${hslMatch[1]}, ${alpha})`

  // Hex or unknown — return as-is (can't add alpha without parsing)
  return color
}

/** Get a theme color with alpha from a CSS variable. */
function themeColor(varName: string, alpha: number, fallback: string): string {
  return withAlpha(cssVar(varName, fallback), alpha)
}

/**
 * Get the current theme's chart colors. Call inside computed() so
 * values are read fresh (reflects current theme/accent hue).
 */
export function getThemeColors() {
  return {
    text: cssVar('--clr-text', FALLBACK_TEXT),
    grid: cssVar('--clr-gray-700', FALLBACK_GRID),
    // Stacked bar pair
    primary: themeColor('--clr-accent', 0.7, 'rgba(54, 162, 235, 0.7)'),
    secondary: themeColor('--clr-subtle', 0.5, 'rgba(201, 203, 207, 0.35)'),
    // Rotating palette from the theme's coordinated semantic colors
    palette: [
      themeColor('--clr-accent', 0.6, 'rgba(54, 162, 235, 0.6)'),
      themeColor('--clr-accent-light', 0.6, 'rgba(255, 205, 86, 0.6)'),
      themeColor('--clr-secondary', 0.6, 'rgba(153, 102, 255, 0.6)'),
      themeColor('--clr-tertiary', 0.6, 'rgba(75, 192, 192, 0.6)'),
      themeColor('--clr-info', 0.6, 'rgba(54, 162, 235, 0.6)'),
      themeColor('--clr-warning', 0.6, 'rgba(255, 159, 64, 0.6)'),
      themeColor('--clr-success', 0.6, 'rgba(99, 200, 132, 0.6)'),
    ],
  }
}

/** Assign rotating theme palette colors to an array of data points. */
export function paletteColors(count: number): string[] {
  const { palette } = getThemeColors()
  return Array.from({ length: count }, (_, i) => palette[i % palette.length]!)
}

/** Common scale/plugin defaults shared by all chart types. */
function baseOptions() {
  return {
    responsive: true,
    layout: { padding: { left: 20, right: 20, bottom: 20 } },
  }
}

function darkScales(opts?: { stacked?: boolean; stepSize?: number }) {
  const { text, grid } = getThemeColors()
  return {
    grid: { color: grid },
    ticks: { color: text, ...(opts?.stepSize ? { stepSize: opts.stepSize } : {}), font: { size: 14 } },
    ...(opts?.stacked ? { stacked: true } : {}),
  }
}

function titlePlugin(text: string) {
  const { text: textColor } = getThemeColors()
  return {
    display: true,
    text,
    color: textColor,
    font: { size: 20 },
    padding: 40,
  }
}

function legendPlugin(show: boolean) {
  const { text } = getThemeColors()
  return {
    display: show,
    ...(show ? { labels: { color: text, font: { size: 14 } } } : {}),
  }
}

/** Horizontal bar chart options (indexAxis: 'y'). Good for category breakdowns. */
export function horizontalBarOptions(title: string, opts?: { stacked?: boolean; legend?: boolean }) {
  const { text } = getThemeColors()
  const stacked = opts?.stacked ?? false
  const legend = opts?.legend ?? false
  return {
    ...baseOptions(),
    indexAxis: 'y' as const,
    scales: {
      x: darkScales({ stacked, stepSize: 1 }),
      y: { ...darkScales({ stacked }), ticks: { color: text, font: { size: 13 } } },
    },
    plugins: {
      legend: legendPlugin(legend),
      title: titlePlugin(title),
    },
  }
}

/** Vertical bar chart options. Good for time series (per-month, per-day). */
export function verticalBarOptions(title: string, data: number[], opts?: { legend?: boolean }) {
  const { text } = getThemeColors()
  const maxVal = data.length > 0 ? Math.max(...data) : 1
  return {
    ...baseOptions(),
    scales: {
      y: {
        beginAtZero: true,
        max: Math.ceil(maxVal * 1.3),
        ...darkScales({ stepSize: 1 }),
      },
      x: { ...darkScales(), ticks: { color: text, font: { size: 13 } } },
    },
    plugins: {
      legend: legendPlugin(opts?.legend ?? false),
      title: titlePlugin(title),
    },
  }
}
