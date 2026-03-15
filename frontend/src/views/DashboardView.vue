<template>
  <div class="dashboard">
    <div class="dashboard__toolbar">
      <h1 class="dashboard__title">Dashboard</h1>
      <div class="dashboard__actions">
        <button
          v-if="!editing"
          class="button button--small"
          @click="startEditing"
        >
          <i class="fa-solid fa-pen"></i> Edit Layout
        </button>
        <template v-else>
          <button
            class="button button--small"
            @click="showWidgetPicker = true"
          >
            <i class="fa-solid fa-plus"></i> Add Widget
          </button>
          <button
            class="button button--small"
            @click="stopEditing"
          >
            <i class="fa-solid fa-check"></i> Done
          </button>
        </template>
      </div>
    </div>

    <div
      ref="gridRef"
      class="grid-stack"
    ></div>

    <!-- Widget picker modal -->
    <Teleport to="body">
      <div
        v-if="showWidgetPicker"
        class="widget-picker-overlay"
        @click.self="showWidgetPicker = false"
      >
        <div class="widget-picker">
          <h3>Add Widget</h3>
          <div class="widget-picker__list">
            <button
              v-for="def in availableWidgets"
              :key="def.type"
              class="widget-picker__item"
              @click="addWidget(def.type)"
            >
              <i :class="def.icon"></i>
              <span>{{ def.name }}</span>
            </button>
          </div>
          <button
            class="button button--small"
            @click="showWidgetPicker = false"
          >
            Close
          </button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { GridStack } from 'gridstack'
import 'gridstack/dist/gridstack.min.css'
import { useDashboard, widgetRegistry, getWidgetType, getWidgetDef } from '@/composables/useDashboard'
import type { DashboardWidgetData } from '@/composables/useDashboard'
import { createLogger } from '@/utils/logger'

const logger = createLogger('DashboardView')

const { editing, loadWidgets, saveWidgets, newWidget, startAutoRefresh, stopAutoRefresh } = useDashboard()
const gridRef = ref<HTMLElement>()
const showWidgetPicker = ref(false)
let grid: GridStack | null = null
const activeWidgetTypes = ref<Set<string>>(new Set())

// Widgets not yet on the dashboard
const availableWidgets = computed(() => widgetRegistry.filter((def) => !activeWidgetTypes.value.has(def.type)))

function renderWidgetContent(type: string): string {
  const def = getWidgetDef(type)
  if (!def) return '<div>Unknown widget</div>'

  const linkMap: Record<string, string> = {
    'tasks-priority': '/tasks',
    countdowns: '/countdowns',
    events: '/events',
    habits: '/habits',
    books: '/books',
    articles: '/articles',
    'money-wasted': '/money-wasted',
    autotasks: '/autotasks',
    durations: '/durations',
  }
  const link = linkMap[type] ?? '/'

  return `
    <div class="dashboard-widget">
      <div class="dashboard-widget__header">
        <div class="dashboard-widget__title">
          <i class="${def.icon}"></i>
          <a href="${link}" class="dashboard-widget__link">${def.name}</a>
        </div>
      </div>
      <div class="dashboard-widget__content" data-widget-type="${type}">
        <div class="widget-placeholder">
          <i class="${def.icon} widget-placeholder__icon"></i>
          <span>${def.name}</span>
        </div>
      </div>
    </div>
  `
}

function syncActiveTypes() {
  if (!grid) return
  const items = grid.save(false) as DashboardWidgetData[]
  activeWidgetTypes.value = new Set(items.map((item) => getWidgetType(item)))
}

function persistLayout() {
  if (!grid) return
  const items = grid.save(false) as DashboardWidgetData[]
  saveWidgets(items)
  syncActiveTypes()
}

function startEditing() {
  editing.value = true
  grid?.enableMove(true)
  grid?.enableResize(true)
}

function stopEditing() {
  editing.value = false
  grid?.enableMove(false)
  grid?.enableResize(false)
  persistLayout()
}

function addWidget(type: string) {
  if (!grid) return
  const widget = newWidget(type)
  if (!widget) return

  // content holds the type string; renderCB generates HTML
  grid.addWidget(widget)
  syncActiveTypes()
  showWidgetPicker.value = false
  logger.info('widget_added', { type })
}

function refreshAllWidgets() {
  // Phase 2 will wire this to store.fetchAll() calls
  logger.info('widgets_refreshed')
}

onMounted(async () => {
  await nextTick()
  if (!gridRef.value) return

  const savedWidgets = loadWidgets()

  // v12 no longer renders content as innerHTML (XSS prevention)
  // renderCB generates HTML from our custom widgetType property
  GridStack.renderCB = (el: HTMLElement, w: DashboardWidgetData) => {
    const type = w.widgetType ?? ''
    el.innerHTML = renderWidgetContent(type)
  }

  grid = GridStack.init(
    {
      cellHeight: 80,
      column: 12,
      margin: 8,
      float: false,
      animate: true,
      resizable: { handles: 'se,sw' },
      disableResize: true,
      disableDrag: true,
      columnOpts: {
        breakpoints: [
          { w: 768, c: 2 },
          { w: 1200, c: 6 },
          { w: 9999, c: 12 },
        ],
      },
    },
    gridRef.value
  )

  // content field holds the widget type string (e.g., 'tasks-priority')
  // renderCB generates the HTML from it
  grid.load(savedWidgets)
  syncActiveTypes()

  grid.on('change', () => {
    if (editing.value) {
      persistLayout()
    }
  })

  // Auto-refresh every 3 minutes
  startAutoRefresh(refreshAllWidgets, 180_000)

  logger.info('dashboard_initialized', { widgetCount: savedWidgets.length })
})

onUnmounted(() => {
  stopAutoRefresh()
  if (grid) {
    grid.destroy(false)
    grid = null
  }
})
</script>

<style scoped>
.dashboard {
  max-width: 100%;
}

.dashboard__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-s);
}

.dashboard__title {
  font-size: var(--fs-600);
  color: var(--clr-text);
  margin: 0;
}

.dashboard__actions {
  display: flex;
  gap: var(--space-xs);
}

/* Widget picker modal */
.widget-picker-overlay {
  position: fixed;
  inset: 0;
  background: var(--clr-black-trans-800);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}

.widget-picker {
  background: var(--clr-gray-900);
  border: 1px solid var(--clr-gray-700);
  border-radius: 0.5rem;
  padding: var(--space-m);
  min-width: 20rem;
  max-width: 90vw;
}

.widget-picker h3 {
  margin-bottom: var(--space-s);
  color: var(--clr-text);
}

.widget-picker__list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2xs);
  margin-bottom: var(--space-m);
  max-height: 50vh;
  overflow-y: auto;
}

.widget-picker__item {
  display: flex;
  align-items: center;
  gap: var(--space-s);
  padding: var(--space-2xs) var(--space-xs);
  background: var(--clr-gray-800);
  border: 1px solid transparent;
  border-radius: 0.375rem;
  color: var(--clr-gray-200);
  cursor: pointer;
  text-align: left;
  font-size: var(--fs-300);
}

.widget-picker__item:hover {
  border-color: var(--clr-accent);
  background: var(--clr-gray-700);
}

.widget-picker__item i {
  color: var(--clr-accent);
  width: 1.5rem;
  text-align: center;
}
</style>

<style>
/* Unscoped styles for gridstack widget content (injected via innerHTML) */
.grid-stack-item-content {
  border-radius: 0.5rem;
  overflow: hidden;
}

.dashboard-widget {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--clr-primary);
  border-radius: 0.5rem;
}

.dashboard-widget__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3xs) var(--space-xs);
  background: var(--clr-primary--lighter);
  border-bottom: 1px solid var(--clr-gray-700);
  min-height: 2rem;
}

.dashboard-widget__title {
  display: flex;
  align-items: center;
  gap: var(--space-2xs);
  font-size: var(--fs-200);
  color: var(--clr-gray-300);
}

.dashboard-widget__title i {
  color: var(--clr-accent);
}

.dashboard-widget__link {
  color: var(--clr-gray-200);
  text-decoration: none;
  font-weight: 600;
}

.dashboard-widget__link:hover {
  color: var(--clr-accent);
}

.dashboard-widget__content {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-2xs) var(--space-xs);
  font-size: var(--fs-200);
}

.widget-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: var(--space-xs);
  color: var(--clr-gray-500);
}

.widget-placeholder__icon {
  font-size: var(--fs-700);
  opacity: 0.3;
}
</style>
