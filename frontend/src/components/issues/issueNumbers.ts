const ISSUE_NUMBER = /^#?(\d+)$/

/** One issue number as a person types it, `812` or `#812`; null when it is not one. */
export function parseIssueNumber(text: string): number | null {
  const match = text.trim().match(ISSUE_NUMBER)
  return match ? Number(match[1]) : null
}

/**
 * Issue numbers separated by commas or spaces. Null when any one of them is
 * not a number, so a typo is refused rather than silently dropped.
 */
export function parseIssueNumbers(text: string): number[] | null {
  const tokens = text.split(/[\s,]+/).filter(Boolean)
  const numbers = tokens.map(parseIssueNumber)
  if (numbers.some((value) => value === null)) return null
  return [...new Set(numbers as number[])]
}
