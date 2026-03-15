import { ref, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { createLogger } from '@/utils/logger'
import type { GridStackWidget } from 'gridstack'

const logger = createLogger('Dashboard')

// Extended GridStackWidget with our custom widgetType property
export interface DashboardWidgetData extends GridStackWidget {
  widgetType?: string
}

export interface WidgetDefinition {
  type: string
  name: string
  icon: string
  defaultW: number
  defaultH: number
  minW?: number
  minH?: number
}

// All available widget types
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

// Default layout for new users
const DEFAULT_WIDGETS: DashboardWidgetData[] = [
  { id: 'w-tasks-priority', x: 0, y: 0, w: 4, h: 3, minW: 3, minH: 2, widgetType: 'tasks-priority' },
  { id: 'w-countdowns', x: 4, y: 0, w: 4, h: 2, minW: 2, minH: 2, widgetType: 'countdowns' },
  { id: 'w-events', x: 8, y: 0, w: 4, h: 3, minW: 3, minH: 2, widgetType: 'events' },
  { id: 'w-habits', x: 4, y: 2, w: 4, h: 3, minW: 3, minH: 2, widgetType: 'habits' },
]

export function getWidgetType(gsWidget: DashboardWidgetData): string {
  // Check widgetType first, fall back to content for backward compatibility
  return gsWidget.widgetType ?? (gsWidget.content as string) ?? ''
}

export function getWidgetDef(type: string): WidgetDefinition | undefined {
  return widgetRegistry.find((w) => w.type === type)
}

export function useDashboard() {
  const auth = useAuthStore()
  const editing = ref(false)
  let refreshInterval: ReturnType<typeof setInterval> | null = null

  function loadWidgets(): DashboardWidgetData[] {
    const saved = auth.preferences?.dashboard_widgets
    if (Array.isArray(saved) && saved.length > 0) {
      logger.info('layout_loaded', { count: saved.length, source: 'preferences' })
      return saved as DashboardWidgetData[]
    }
    logger.info('layout_loaded', { count: DEFAULT_WIDGETS.length, source: 'defaults' })
    return [...DEFAULT_WIDGETS]
  }

  async function saveWidgets(widgets: DashboardWidgetData[]) {
    // Strip any HTML content that gridstack might have saved, keep only layout + widgetType
    const clean = widgets.map((w) => ({
      id: w.id,
      x: w.x,
      y: w.y,
      w: w.w,
      h: w.h,
      minW: w.minW,
      minH: w.minH,
      widgetType: w.widgetType,
    }))
    try {
      await auth.updatePreferences({ dashboard_widgets: clean })
      logger.info('layout_saved', { count: clean.length })
    } catch (e) {
      logger.error('layout_save_failed', { error: String(e) })
    }
  }

  function createWidgetId(type: string): string {
    return `w-${type}-${Date.now()}`
  }

  function newWidget(type: string): DashboardWidgetData | null {
    const def = getWidgetDef(type)
    if (!def) return null
    return {
      id: createWidgetId(type),
      w: def.defaultW,
      h: def.defaultH,
      minW: def.minW,
      minH: def.minH,
      widgetType: type,
    }
  }

  // Auto-refresh: call a callback every N ms
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

  onUnmounted(() => {
    stopAutoRefresh()
  })

  return {
    editing,
    loadWidgets,
    saveWidgets,
    newWidget,
    startAutoRefresh,
    stopAutoRefresh,
  }
}
