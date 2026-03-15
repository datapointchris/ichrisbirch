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
    >
      <div
        v-for="widget in widgets"
        :key="widget.id"
        class="grid-stack-item"
        :gs-id="widget.id"
        :gs-x="widget.x"
        :gs-y="widget.y"
        :gs-w="widget.w"
        :gs-h="widget.h"
        :gs-min-w="widget.minW"
        :gs-min-h="widget.minH"
      >
        <div class="grid-stack-item-content">
          <DashboardWidget
            :title="getWidgetTitle(widget)"
            :icon="getWidgetIcon(widget)"
            :link-to="getWidgetLink(widget)"
            :editing="editing"
            @remove="removeWidget(widget.id!)"
          >
            <component :is="getWidgetComponent(widget)" />
          </DashboardWidget>
        </div>
      </div>
    </div>

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
import { ref, computed, onMounted, onUnmounted, nextTick, type Component, markRaw } from 'vue'
import { GridStack } from 'gridstack'
import 'gridstack/dist/gridstack.min.css'
import { useDashboard, widgetRegistry, getWidgetType, getWidgetDef } from '@/composables/useDashboard'
import type { DashboardWidgetData } from '@/composables/useDashboard'
import { createLogger } from '@/utils/logger'
import DashboardWidget from '@/components/dashboard/DashboardWidget.vue'
import WidgetTasksPriority from '@/components/dashboard/WidgetTasksPriority.vue'
import WidgetCountdowns from '@/components/dashboard/WidgetCountdowns.vue'
import WidgetEvents from '@/components/dashboard/WidgetEvents.vue'
import WidgetHabits from '@/components/dashboard/WidgetHabits.vue'

const logger = createLogger('DashboardView')

const { editing, loadWidgets, saveWidgets, newWidget, startAutoRefresh, stopAutoRefresh } = useDashboard()
const gridRef = ref<HTMLElement>()
const showWidgetPicker = ref(false)
let grid: GridStack | null = null
const widgets = ref<DashboardWidgetData[]>([])

// Component map for dynamic rendering
const widgetComponents: Record<string, Component> = {
  'tasks-priority': markRaw(WidgetTasksPriority),
  countdowns: markRaw(WidgetCountdowns),
  events: markRaw(WidgetEvents),
  habits: markRaw(WidgetHabits),
}

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

// Widgets not yet on the dashboard
const activeWidgetTypes = computed(() => new Set(widgets.value.map((w) => getWidgetType(w))))
const availableWidgets = computed(() => widgetRegistry.filter((def) => !activeWidgetTypes.value.has(def.type)))

function getWidgetTitle(w: DashboardWidgetData): string {
  const def = getWidgetDef(getWidgetType(w))
  return def?.name ?? 'Unknown'
}

function getWidgetIcon(w: DashboardWidgetData): string {
  const def = getWidgetDef(getWidgetType(w))
  return def?.icon ?? 'fa-solid fa-question'
}

function getWidgetLink(w: DashboardWidgetData): string {
  return linkMap[getWidgetType(w)] ?? '/'
}

function getWidgetComponent(w: DashboardWidgetData): Component | null {
  return widgetComponents[getWidgetType(w)] ?? null
}

function persistLayout() {
  if (!grid) return
  // Read positions from gridstack, merge with our widgetType data
  const gsItems = grid.getGridItems()
  const updated: DashboardWidgetData[] = []
  for (const el of gsItems) {
    const node = el.gridstackNode
    if (!node) continue
    const existing = widgets.value.find((w) => w.id === node.id)
    updated.push({
      id: node.id,
      x: node.x,
      y: node.y,
      w: node.w,
      h: node.h,
      minW: node.minW,
      minH: node.minH,
      widgetType: existing?.widgetType ?? getWidgetType(existing ?? {}),
    })
  }
  widgets.value = updated
  saveWidgets(updated)
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

async function addWidget(type: string) {
  if (!grid) return
  const widget = newWidget(type)
  if (!widget) return

  widgets.value.push(widget)
  await nextTick()

  // Tell gridstack about the new DOM element
  const el = gridRef.value?.querySelector(`[gs-id="${widget.id}"]`) as HTMLElement
  if (el) {
    grid.makeWidget(el)
  }

  showWidgetPicker.value = false
  persistLayout()
  logger.info('widget_added', { type })
}

function removeWidget(id: string) {
  if (!grid) return
  const el = gridRef.value?.querySelector(`[gs-id="${id}"]`) as HTMLElement
  if (el) {
    grid.removeWidget(el, true, false)
  }
  widgets.value = widgets.value.filter((w) => w.id !== id)
  persistLayout()
  logger.info('widget_removed', { id })
}

function refreshAllWidgets() {
  logger.info('widgets_refreshed')
  // Each widget component handles its own data fetching via onMounted
  // Force re-fetch by... TODO in Phase 3 if needed
}

onMounted(async () => {
  widgets.value = loadWidgets()

  await nextTick()
  if (!gridRef.value) return

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

  grid.on('change', () => {
    if (editing.value) {
      persistLayout()
    }
  })

  startAutoRefresh(refreshAllWidgets, 180_000)
  logger.info('dashboard_initialized', { widgetCount: widgets.value.length })
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
/* Unscoped: gridstack item content and widget list styles */
.grid-stack-item-content {
  border-radius: 0.5rem;
  overflow: hidden;
}

.widget-list {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.widget-list__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3xs) 0;
  border-bottom: 1px solid var(--clr-gray-800);
}

.widget-list__item--done {
  opacity: 0.5;
}

.widget-list__name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.widget-list__meta {
  display: flex;
  align-items: center;
  gap: var(--space-2xs);
  color: var(--clr-gray-400);
  font-size: var(--fs-200);
  flex-shrink: 0;
}

.widget-list__tag {
  font-size: 0.6rem;
  color: var(--clr-gray-500);
  text-transform: uppercase;
}

.widget-action-btn {
  background: none;
  border: 1px solid var(--clr-gray-600);
  color: var(--clr-gray-400);
  cursor: pointer;
  border-radius: 50%;
  width: 1.5rem;
  height: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  padding: 0;
  line-height: 1;
}

.widget-action-btn:hover {
  border-color: var(--clr-accent);
  color: var(--clr-accent);
}

.widget-action-btn--active {
  border-color: var(--clr-accent);
  color: var(--clr-accent);
}

.widget-loading {
  color: var(--clr-gray-500);
  text-align: center;
  padding: var(--space-m);
}

.widget-empty {
  color: var(--clr-gray-500);
  text-align: center;
  padding: var(--space-s);
  font-style: italic;
}
</style>
