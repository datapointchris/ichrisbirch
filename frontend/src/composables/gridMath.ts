/**
 * Grid math utilities for the dashboard layout engine.
 *
 * All functions here are pure — they take data in and return data out,
 * with no Vue reactivity, no DOM access, and no side effects.
 * This makes them independently testable and reusable.
 */

import type { VueDashItem } from './useVueDash'

// Grid configuration
export const CELL_HEIGHT = 40
export const GAP = 8

// The widget registry defines sizes in "visual rows" (e.g., defaultH: 3 means
// "3 rows tall at 80px each"). The grid uses half-height rows (40px) for finer
// resize snapping. ROW_SCALE converts between the two: a visual row of 3 becomes
// a grid rowSpan of 6. Change this to 3 or 4 for even finer granularity.
export const ROW_SCALE = 2

/**
 * AABB (axis-aligned bounding box) collision test.
 * Returns true if a rectangle at (col, row) with the given span
 * overlaps any existing item. Optionally excludes one item by ID
 * (useful when checking "can I move this item here?").
 *
 * The math: two rectangles overlap when ALL four of these are true:
 *   - a.left < b.right     (col < item.col + item.colSpan)
 *   - a.right > b.left     (col + colSpan > item.col)
 *   - a.top < b.bottom     (row < item.row + item.rowSpan)
 *   - a.bottom > b.top     (row + rowSpan > item.row)
 * If any one is false, the rectangles don't overlap.
 */
export function isOccupied(items: VueDashItem[], col: number, row: number, colSpan: number, rowSpan: number, excludeId?: string): boolean {
  for (const item of items) {
    if (item.id === excludeId) continue
    if (col < item.col + item.colSpan && col + colSpan > item.col && row < item.row + item.rowSpan && row + rowSpan > item.row) {
      return true
    }
  }
  return false
}

/**
 * Scan the grid top-to-bottom, left-to-right for the first position
 * where a widget of the given size fits without overlapping anything.
 *
 * The 100-row limit is a safety bound — in practice, widgets rarely
 * go past row 20. If no position is found (shouldn't happen), falls
 * back to (0, 0).
 */
export function findOpenPosition(items: VueDashItem[], colSpan: number, rowSpan: number, columns: number): { col: number; row: number } {
  const MAX_ROWS = 100
  for (let row = 0; row < MAX_ROWS; row++) {
    for (let col = 0; col <= columns - colSpan; col++) {
      if (!isOccupied(items, col, row, colSpan, rowSpan)) {
        return { col, row }
      }
    }
  }
  return { col: 0, row: 0 }
}

/**
 * When the viewport changes breakpoints (e.g., 12 cols → 6 cols),
 * widgets that were at col 8 with colSpan 4 would overflow.
 * This clamps every item's col + colSpan to fit within the new column count.
 *
 * Note: this does NOT compact (push items upward). Items stay at their
 * row positions — only horizontal overflow is fixed.
 */
export function reflowForColumns(items: VueDashItem[], newCols: number): VueDashItem[] {
  return items.map((item) => {
    const colSpan = Math.min(item.colSpan, newCols)
    const col = Math.min(item.col, Math.max(0, newCols - colSpan))
    return { ...item, col, colSpan }
  })
}

/**
 * Convert a pixel coordinate (from a pointer event) to a grid cell.
 *
 * The grid has columns of equal width with gaps between them.
 * cellWidth = (containerWidth - gaps) / columns
 * Then we divide the relative X/Y by (cellWidth + gap) to get the cell index.
 *
 * The result is clamped so it never returns a negative cell or one
 * beyond the grid bounds.
 */
export function pointerToGridCell(clientX: number, clientY: number, containerRect: DOMRect, columns: number): { col: number; row: number } {
  const cellWidth = (containerRect.width - GAP * (columns - 1)) / columns
  const relX = clientX - containerRect.left
  const relY = clientY - containerRect.top
  const col = Math.max(0, Math.min(columns - 1, Math.floor(relX / (cellWidth + GAP))))
  const row = Math.max(0, Math.floor(relY / (CELL_HEIGHT + GAP)))
  return { col, row }
}

/**
 * Calculate the bottom edge of the lowest widget.
 * Used to determine grid container height and how many extra rows
 * to show below the widgets.
 */
export function maxRow(items: VueDashItem[]): number {
  if (items.length === 0) return 0
  return Math.max(...items.map((i) => i.row + i.rowSpan))
}

/**
 * Calculate the pixel width of one grid cell given the container width.
 * Accounts for gaps between columns.
 */
export function cellWidth(containerWidth: number, columns: number): number {
  return (containerWidth - GAP * (columns - 1)) / columns
}
