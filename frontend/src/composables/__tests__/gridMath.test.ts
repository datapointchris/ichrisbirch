import { describe, it, expect } from 'vitest'
import { isOccupied, findOpenPosition, reflowForColumns, pointerToGridCell } from '../gridMath'
import type { VueDashItem } from '../useVueDash'

// Helper to create a minimal VueDashItem for testing
function item(overrides: Partial<VueDashItem> & { id: string }): VueDashItem {
  return {
    widgetType: 'test',
    col: 0,
    row: 0,
    colSpan: 1,
    rowSpan: 1,
    minColSpan: 1,
    minRowSpan: 1,
    ...overrides,
  }
}

describe('isOccupied', () => {
  it('returns false for empty grid', () => {
    expect(isOccupied([], 0, 0, 4, 4)).toBe(false)
  })

  it('detects direct overlap', () => {
    const items = [item({ id: 'a', col: 0, row: 0, colSpan: 4, rowSpan: 4 })]
    expect(isOccupied(items, 2, 2, 3, 3)).toBe(true)
  })

  it('detects partial overlap on right edge', () => {
    const items = [item({ id: 'a', col: 0, row: 0, colSpan: 4, rowSpan: 4 })]
    expect(isOccupied(items, 3, 0, 2, 1)).toBe(true)
  })

  it('returns false for adjacent non-overlapping items', () => {
    const items = [item({ id: 'a', col: 0, row: 0, colSpan: 4, rowSpan: 4 })]
    // Immediately to the right — no overlap
    expect(isOccupied(items, 4, 0, 4, 4)).toBe(false)
  })

  it('returns false for items below', () => {
    const items = [item({ id: 'a', col: 0, row: 0, colSpan: 4, rowSpan: 4 })]
    expect(isOccupied(items, 0, 4, 4, 4)).toBe(false)
  })

  it('excludes item by ID', () => {
    const items = [item({ id: 'a', col: 0, row: 0, colSpan: 4, rowSpan: 4 })]
    // Would overlap, but we exclude 'a'
    expect(isOccupied(items, 0, 0, 4, 4, 'a')).toBe(false)
  })

  it('still detects overlap with other items when excluding one', () => {
    const items = [item({ id: 'a', col: 0, row: 0, colSpan: 4, rowSpan: 4 }), item({ id: 'b', col: 4, row: 0, colSpan: 4, rowSpan: 4 })]
    // Exclude 'a' but still overlaps with 'b'
    expect(isOccupied(items, 5, 1, 2, 2, 'a')).toBe(true)
  })
})

describe('findOpenPosition', () => {
  it('returns (0,0) for empty grid', () => {
    expect(findOpenPosition([], 4, 4, 12)).toEqual({ col: 0, row: 0 })
  })

  it('finds position to the right of existing item', () => {
    const items = [item({ id: 'a', col: 0, row: 0, colSpan: 4, rowSpan: 4 })]
    expect(findOpenPosition(items, 4, 4, 12)).toEqual({ col: 4, row: 0 })
  })

  it('wraps to next row when row is full', () => {
    const items = [item({ id: 'a', col: 0, row: 0, colSpan: 6, rowSpan: 2 }), item({ id: 'b', col: 6, row: 0, colSpan: 6, rowSpan: 2 })]
    // Row 0 is full (12 columns used), widget needs 4 cols
    expect(findOpenPosition(items, 4, 2, 12)).toEqual({ col: 0, row: 2 })
  })

  it('finds gap between items', () => {
    const items = [item({ id: 'a', col: 0, row: 0, colSpan: 3, rowSpan: 2 }), item({ id: 'b', col: 7, row: 0, colSpan: 5, rowSpan: 2 })]
    // Gap from col 3-6 (4 columns wide)
    expect(findOpenPosition(items, 4, 2, 12)).toEqual({ col: 3, row: 0 })
  })
})

describe('reflowForColumns', () => {
  it('clamps colSpan to new column count', () => {
    const items = [item({ id: 'a', col: 0, row: 0, colSpan: 8, rowSpan: 2 })]
    const reflowed = reflowForColumns(items, 6)
    expect(reflowed[0].colSpan).toBe(6)
  })

  it('moves item leftward if it would overflow', () => {
    const items = [item({ id: 'a', col: 8, row: 0, colSpan: 4, rowSpan: 2 })]
    const reflowed = reflowForColumns(items, 6)
    // colSpan stays 4 (fits), col pushed left so right edge = 6 (col 2 + span 4)
    expect(reflowed[0].col).toBe(2)
    expect(reflowed[0].colSpan).toBe(4)
  })

  it('does not modify items that already fit', () => {
    const items = [item({ id: 'a', col: 0, row: 0, colSpan: 4, rowSpan: 2 })]
    const reflowed = reflowForColumns(items, 12)
    expect(reflowed[0].col).toBe(0)
    expect(reflowed[0].colSpan).toBe(4)
  })

  it('preserves row positions', () => {
    const items = [item({ id: 'a', col: 0, row: 5, colSpan: 4, rowSpan: 2 })]
    const reflowed = reflowForColumns(items, 6)
    expect(reflowed[0].row).toBe(5)
  })
})

describe('pointerToGridCell', () => {
  // Simulate a 1000px wide container with 12 columns and 8px gaps
  // cellWidth = (1000 - 8 * 11) / 12 = (1000 - 88) / 12 = 76px
  // Each cell + gap = 76 + 8 = 84px
  const rect = { left: 100, top: 50, width: 1000, height: 500 } as DOMRect

  it('returns (0,0) for top-left corner', () => {
    const cell = pointerToGridCell(100, 50, rect, 12)
    expect(cell.col).toBe(0)
    expect(cell.row).toBe(0)
  })

  it('clamps negative coordinates to (0,0)', () => {
    const cell = pointerToGridCell(50, 20, rect, 12)
    expect(cell.col).toBe(0)
    expect(cell.row).toBe(0)
  })

  it('clamps to max column', () => {
    const cell = pointerToGridCell(1200, 50, rect, 12)
    expect(cell.col).toBe(11)
  })

  it('calculates mid-grid cell correctly', () => {
    // Column 5 starts at approximately 5 * 84 = 420px from container left
    const cell = pointerToGridCell(100 + 425, 50, rect, 12)
    expect(cell.col).toBe(5)
  })
})
