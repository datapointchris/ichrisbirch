import { ref, computed, onMounted, onUnmounted, type CSSProperties } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { createLogger } from '@/utils/logger'
import { CELL_HEIGHT, GAP, ROW_SCALE, findOpenPosition, reflowForColumns, pointerToGridCell, maxRow, cellWidth } from './gridMath'

const logger = createLogger('Dashboard')

// --- Types ---

export interface WidgetDefinition {
  type: string
  name: string
  icon: string
  defaultW: number
  defaultH: number
  minW?: number
  minH?: number
}

export interface VueDashItem {
  id: string
  widgetType: string
  col: number
  row: number
  colSpan: number
  rowSpan: number
  minColSpan: number
  minRowSpan: number
}

export interface DragState {
  itemId: string
  targetCol: number
  targetRow: number
  // Pixel offset from item's original position (for smooth CSS transform)
  translateX: number
  translateY: number
  // Pointer offset within the item element (so cursor stays at grab point)
  gripOffsetX: number
  gripOffsetY: number
  // Item's original pixel position in the grid
  originX: number
  originY: number
}

export type ResizeDirection = 'se' | 'sw'

export interface ResizeState {
  itemId: string
  direction: ResizeDirection
  startCol: number
  startColSpan: number
  startRowSpan: number
  startPointerX: number
  startPointerY: number
  startLeft: number
  startTop: number
  startWidth: number
  startHeight: number
  currentLeft: number
  currentWidth: number
  currentHeight: number
  targetCol: number
  targetColSpan: number
  targetRowSpan: number
}

// --- Widget registry ---

export const widgetRegistry: WidgetDefinition[] = [
  { type: 'tasks-priority', name: 'Tasks (Priority)', icon: 'fa-solid fa-list-check', defaultW: 4, defaultH: 3, minW: 3, minH: 2 },
  { type: 'countdowns', name: 'Countdowns', icon: 'fa-solid fa-hourglass-half', defaultW: 4, defaultH: 2, minW: 2, minH: 2 },
  { type: 'events', name: 'Events', icon: 'fa-solid fa-calendar', defaultW: 4, defaultH: 3, minW: 3, minH: 2 },
  { type: 'habits', name: 'Habits', icon: 'fa-solid fa-repeat', defaultW: 4, defaultH: 3, minW: 3, minH: 2 },
  { type: 'books', name: 'Books', icon: 'fa-solid fa-book', defaultW: 4, defaultH: 2, minW: 2, minH: 2 },
  { type: 'articles', name: 'Articles', icon: 'fa-solid fa-newspaper', defaultW: 4, defaultH: 2, minW: 3, minH: 2 },
  { type: 'money-wasted', name: 'Money Wasted', icon: 'fa-solid fa-money-bill-wave', defaultW: 3, defaultH: 2, minW: 2, minH: 2 },
  { type: 'autotasks', name: 'AutoTasks', icon: 'fa-solid fa-robot', defaultW: 4, defaultH: 2, minW: 3, minH: 2 },
  { type: 'durations', name: 'Durations', icon: 'fa-solid fa-clock-rotate-left', defaultW: 4, defaultH: 2, minW: 2, minH: 2 },
]

export function getWidgetDef(type: string): WidgetDefinition | undefined {
  return widgetRegistry.find((w) => w.type === type)
}

// --- Defaults ---

// Row/rowSpan values are pre-scaled by ROW_SCALE (e.g., rowSpan: 6 = 3 visual rows × ROW_SCALE of 2)
const DEFAULT_ITEMS: VueDashItem[] = [
  { id: 'w-tasks-priority', widgetType: 'tasks-priority', col: 0, row: 0, colSpan: 4, rowSpan: 6, minColSpan: 3, minRowSpan: 4 },
  { id: 'w-countdowns', widgetType: 'countdowns', col: 4, row: 0, colSpan: 4, rowSpan: 4, minColSpan: 2, minRowSpan: 4 },
  { id: 'w-events', widgetType: 'events', col: 8, row: 0, colSpan: 4, rowSpan: 6, minColSpan: 3, minRowSpan: 4 },
  { id: 'w-habits', widgetType: 'habits', col: 4, row: 4, colSpan: 4, rowSpan: 6, minColSpan: 3, minRowSpan: 4 },
]

// --- Composable ---

/**
 * Update one item in the items array by ID, applying a partial update.
 * Returns a new array (immutable update pattern for Vue reactivity).
 *
 * Partial<VueDashItem> means "an object with some or all of VueDashItem's
 * fields." TypeScript verifies that every field you pass is a valid
 * VueDashItem field with the correct type — no casts needed.
 */
function updateItem(items: VueDashItem[], id: string, patch: Partial<VueDashItem>): VueDashItem[] {
  return items.map((item) => (item.id === id ? { ...item, ...patch } : item))
}

export function useVueDash() {
  const auth = useAuthStore()
  const items = ref<VueDashItem[]>([])
  const columns = ref(12)
  const dragState = ref<DragState | null>(null)
  const resizeState = ref<ResizeState | null>(null)
  let refreshInterval: ReturnType<typeof setInterval> | null = null

  /** Look up a widget by ID. Returns undefined if not found (e.g., removed during drag). */
  function getItem(id: string): VueDashItem | undefined {
    return items.value.find((i) => i.id === id)
  }

  // Responsive breakpoints — store cleanup functions so we can remove listeners on unmount
  const breakpointCleanups: (() => void)[] = []

  function setupBreakpoints() {
    const breakpoints = [
      { media: '(max-width: 767px)', cols: 2 },
      { media: '(min-width: 768px) and (max-width: 1199px)', cols: 6 },
      { media: '(min-width: 1200px)', cols: 12 },
    ]
    for (const bp of breakpoints) {
      const mql = window.matchMedia(bp.media)
      const handler = () => {
        if (mql.matches) {
          const oldCols = columns.value
          columns.value = bp.cols
          if (oldCols !== bp.cols) {
            items.value = reflowForColumns(items.value, bp.cols)
            logger.info('breakpoint_changed', { from: oldCols, to: bp.cols })
          }
        }
      }
      mql.addEventListener('change', handler)
      // Store a cleanup function that captures both mql and handler references
      breakpointCleanups.push(() => mql.removeEventListener('change', handler))
      // Set initial column count
      if (mql.matches) {
        columns.value = bp.cols
      }
    }
  }

  function teardownBreakpoints() {
    breakpointCleanups.forEach((cleanup) => cleanup())
    breakpointCleanups.length = 0
  }

  // Minimum grid height: tallest widget + 2 extra rows for breathing room
  const gridRows = computed(() => Math.max(4, maxRow(items.value) + 2))

  const gridStyle = computed(
    (): CSSProperties => ({
      display: 'grid',
      gridTemplateColumns: `repeat(${columns.value}, 1fr)`,
      gridAutoRows: `${CELL_HEIGHT}px`,
      gap: `${GAP}px`,
      minHeight: `${gridRows.value * (CELL_HEIGHT + GAP) - GAP}px`,
    })
  )

  function itemStyle(item: VueDashItem): CSSProperties {
    return {
      gridColumn: `${item.col + 1} / span ${item.colSpan}`,
      gridRow: `${item.row + 1} / span ${item.rowSpan}`,
    }
  }

  // --- Layout persistence ---

  function loadLayout(): VueDashItem[] {
    const saved = auth.preferences?.dashboard_widgets
    if (Array.isArray(saved) && saved.length > 0) {
      // Migrate from old GridStack format (x/y/w/h) if needed
      const migrated = (saved as Record<string, unknown>[]).map((item) => {
        if ('colSpan' in item) return item as unknown as VueDashItem
        // Old format: x, y, w, h → col, row, colSpan, rowSpan (with half-height row doubling)
        const oldW = (item.w as number) ?? 4
        const oldH = (item.h as number) ?? 3
        return {
          id: (item.id as string) ?? `w-${item.widgetType}-${Date.now()}`,
          widgetType: (item.widgetType as string) ?? '',
          col: (item.x as number) ?? 0,
          row: ((item.y as number) ?? 0) * ROW_SCALE,
          colSpan: oldW,
          rowSpan: oldH * ROW_SCALE,
          minColSpan: (item.minW as number) ?? 2,
          minRowSpan: ((item.minH as number) ?? 2) * ROW_SCALE,
        } as VueDashItem
      })
      logger.info('layout_loaded', { count: migrated.length, source: 'preferences' })
      return migrated
    }
    logger.info('layout_loaded', { count: DEFAULT_ITEMS.length, source: 'defaults' })
    return [...DEFAULT_ITEMS]
  }

  async function saveLayout() {
    const clean = items.value.map((item) => ({
      id: item.id,
      widgetType: item.widgetType,
      col: item.col,
      row: item.row,
      colSpan: item.colSpan,
      rowSpan: item.rowSpan,
      minColSpan: item.minColSpan,
      minRowSpan: item.minRowSpan,
    }))
    try {
      await auth.updatePreferences({ dashboard_widgets: clean })
      logger.info('layout_saved', { count: clean.length })
    } catch (e) {
      logger.error('layout_save_failed', { error: String(e) })
    }
  }

  // --- Widget management ---

  function addItem(type: string) {
    const def = getWidgetDef(type)
    if (!def) return
    const id = `w-${type}-${Date.now()}`
    const colSpan = Math.min(def.defaultW, columns.value)
    const rowSpan = def.defaultH * ROW_SCALE
    const pos = findOpenPosition(items.value, colSpan, rowSpan, columns.value)
    const newItem: VueDashItem = {
      id,
      widgetType: type,
      col: pos.col,
      row: pos.row,
      colSpan,
      rowSpan,
      minColSpan: def.minW ?? 2,
      minRowSpan: (def.minH ?? 2) * ROW_SCALE,
    }
    items.value = [...items.value, newItem]
    saveLayout()
    logger.info('widget_added', { type })
  }

  function removeItem(id: string) {
    items.value = items.value.filter((i) => i.id !== id)
    saveLayout()
    logger.info('widget_removed', { id })
  }

  // --- Drag handlers (Pointer Events for smooth movement) ---

  function startDrag(itemId: string, event: PointerEvent, itemEl: HTMLElement, containerEl: HTMLElement) {
    event.preventDefault()
    const item = getItem(itemId)
    if (!item) return

    // Capture pointer so we get all move events even outside the element
    itemEl.setPointerCapture(event.pointerId)

    const itemRect = itemEl.getBoundingClientRect()
    const containerRect = containerEl.getBoundingClientRect()

    dragState.value = {
      itemId,
      targetCol: item.col,
      targetRow: item.row,
      translateX: 0,
      translateY: 0,
      gripOffsetX: event.clientX - itemRect.left,
      gripOffsetY: event.clientY - itemRect.top,
      originX: itemRect.left - containerRect.left,
      originY: itemRect.top - containerRect.top,
    }
  }

  function handleDragMove(event: PointerEvent, containerEl: HTMLElement) {
    if (!dragState.value) return
    event.preventDefault()
    const ds = dragState.value
    const item = getItem(ds.itemId)
    if (!item) return

    const containerRect = containerEl.getBoundingClientRect()

    // Pixel position of pointer relative to container, adjusted for grip point
    const pointerInContainerX = event.clientX - containerRect.left - ds.gripOffsetX
    const pointerInContainerY = event.clientY - containerRect.top - ds.gripOffsetY

    // Smooth pixel translate (item follows cursor exactly)
    ds.translateX = pointerInContainerX - ds.originX
    ds.translateY = pointerInContainerY - ds.originY

    // Compute target grid cell for drop position
    const cell = pointerToGridCell(event.clientX - ds.gripOffsetX, event.clientY - ds.gripOffsetY, containerRect, columns.value)
    ds.targetCol = Math.min(Math.max(0, cell.col), columns.value - item.colSpan)
    ds.targetRow = Math.max(0, cell.row)
  }

  function handleDrop() {
    if (!dragState.value) return
    const ds = dragState.value
    items.value = updateItem(items.value, ds.itemId, { col: ds.targetCol, row: ds.targetRow })
    saveLayout()
    logger.info('widget_moved', { id: ds.itemId, col: ds.targetCol, row: ds.targetRow })
    dragState.value = null
  }

  function dragTransform(): CSSProperties {
    if (!dragState.value) return {}
    return {
      transform: `translate(${dragState.value.translateX}px, ${dragState.value.translateY}px)`,
    }
  }

  // --- Resize handlers (Pointer Events) ---

  function startResize(itemId: string, direction: ResizeDirection, event: PointerEvent, itemEl: HTMLElement, containerEl: HTMLElement) {
    event.preventDefault()
    event.stopPropagation()
    const item = getItem(itemId)
    if (!item) return

    const itemRect = itemEl.getBoundingClientRect()
    const containerRect = containerEl.getBoundingClientRect()

    resizeState.value = {
      itemId,
      direction,
      startCol: item.col,
      startColSpan: item.colSpan,
      startRowSpan: item.rowSpan,
      startPointerX: event.clientX,
      startPointerY: event.clientY,
      startLeft: itemRect.left - containerRect.left,
      startTop: itemRect.top - containerRect.top,
      startWidth: itemRect.width,
      startHeight: itemRect.height,
      currentLeft: itemRect.left - containerRect.left,
      currentWidth: itemRect.width,
      currentHeight: itemRect.height,
      targetCol: item.col,
      targetColSpan: item.colSpan,
      targetRowSpan: item.rowSpan,
    }
    ;(event.target as HTMLElement).setPointerCapture(event.pointerId)
  }

  function handleResizeMove(event: PointerEvent, containerEl: HTMLElement) {
    if (!resizeState.value) return
    const rs = resizeState.value
    const item = getItem(rs.itemId)
    if (!item) return

    const rect = containerEl.getBoundingClientRect()
    const cw = cellWidth(rect.width, columns.value)

    const deltaX = event.clientX - rs.startPointerX
    const deltaY = event.clientY - rs.startPointerY

    const minWidth = item.minColSpan * cw + (item.minColSpan - 1) * GAP
    const minHeight = item.minRowSpan * CELL_HEIGHT + (item.minRowSpan - 1) * GAP

    if (rs.direction === 'se') {
      // Bottom-right: grow rightward and downward
      rs.currentWidth = Math.max(minWidth, rs.startWidth + deltaX)
      rs.currentHeight = Math.max(minHeight, rs.startHeight + deltaY)
      rs.currentLeft = rs.startLeft

      const deltaCols = Math.round(deltaX / (cw + GAP))
      const deltaRows = Math.round(deltaY / (CELL_HEIGHT + GAP))
      rs.targetCol = rs.startCol
      rs.targetColSpan = Math.max(item.minColSpan, Math.min(columns.value - rs.startCol, rs.startColSpan + deltaCols))
      rs.targetRowSpan = Math.max(item.minRowSpan, rs.startRowSpan + deltaRows)
    } else {
      // Bottom-left: grow leftward (left edge moves, right edge stays) and downward
      const newWidth = Math.max(minWidth, rs.startWidth - deltaX)
      rs.currentWidth = newWidth
      rs.currentHeight = Math.max(minHeight, rs.startHeight + deltaY)
      rs.currentLeft = rs.startLeft + (rs.startWidth - newWidth)

      const deltaCols = Math.round(-deltaX / (cw + GAP))
      const deltaRows = Math.round(deltaY / (CELL_HEIGHT + GAP))
      const newColSpan = Math.max(item.minColSpan, rs.startColSpan + deltaCols)
      const newCol = Math.max(0, rs.startCol - (newColSpan - rs.startColSpan))
      rs.targetCol = newCol
      rs.targetColSpan = Math.min(newColSpan, rs.startCol + rs.startColSpan)
      rs.targetRowSpan = Math.max(item.minRowSpan, rs.startRowSpan + deltaRows)
    }
  }

  function resizeStyle(): CSSProperties {
    if (!resizeState.value) return {}
    const rs = resizeState.value
    return {
      position: 'absolute',
      left: `${rs.currentLeft}px`,
      top: `${rs.startTop}px`,
      width: `${rs.currentWidth}px`,
      height: `${rs.currentHeight}px`,
      gridColumn: 'auto',
      gridRow: 'auto',
      zIndex: '50',
    }
  }

  function handleResizeEnd() {
    if (!resizeState.value) return
    const rs = resizeState.value
    items.value = updateItem(items.value, rs.itemId, {
      col: rs.targetCol,
      colSpan: rs.targetColSpan,
      rowSpan: rs.targetRowSpan,
    })
    resizeState.value = null
    saveLayout()
    logger.info('widget_resized')
  }

  // --- Auto-refresh ---

  function startAutoRefresh(callback: () => void, intervalMs = 180_000) {
    stopAutoRefresh()
    refreshInterval = setInterval(() => {
      logger.info('auto_refresh')
      callback()
    }, intervalMs)
  }

  function stopAutoRefresh() {
    if (refreshInterval) {
      clearInterval(refreshInterval)
      refreshInterval = null
    }
  }

  // --- Active widget types (for widget picker) ---

  const activeWidgetTypes = computed(() => new Set(items.value.map((i) => i.widgetType)))
  const availableWidgets = computed(() => widgetRegistry.filter((def) => !activeWidgetTypes.value.has(def.type)))

  // --- Lifecycle ---

  onMounted(() => {
    setupBreakpoints()
  })

  onUnmounted(() => {
    stopAutoRefresh()
    teardownBreakpoints()
  })

  return {
    // Reactive state
    items,
    dragState,
    resizeState,

    // Computed styles
    gridStyle,
    itemStyle,
    dragTransform,
    resizeStyle,

    // Widget management
    availableWidgets,
    loadLayout,
    addItem,
    removeItem,

    // Drag handlers
    startDrag,
    handleDragMove,
    handleDrop,

    // Resize handlers
    startResize,
    handleResizeMove,
    handleResizeEnd,

    // Auto-refresh
    startAutoRefresh,
    stopAutoRefresh,
  }
}
