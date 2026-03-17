<template>
  <div class="vuedash">
    <div class="vuedash__toolbar">
      <h1 class="vuedash__title">Dashboard</h1>
      <button
        class="button button--small"
        @click="showWidgetPicker = true"
      >
        <i class="fa-solid fa-plus"></i> Add Widget
      </button>
    </div>

    <div
      ref="gridRef"
      class="vuedash__grid"
      :style="gridStyle"
    >
      <div
        v-for="item in items"
        :key="item.id"
        :ref="(el) => setItemRef(item.id, el as HTMLElement)"
        class="vuedash__item"
        :class="{
          'vuedash__item--dragging': dragState?.itemId === item.id,
          'vuedash__item--snapping': !!snapAnimations[item.id],
        }"
        :style="[
          itemStyle(item),
          dragState?.itemId === item.id ? dragTransform() : {},
          resizeState?.itemId === item.id ? resizeStyle() : {},
          snapAnimations[item.id] ?? {},
        ]"
      >
        <DashboardWidget
          :title="getWidgetTitle(item)"
          :icon="getWidgetIcon(item)"
          :link-to="getWidgetLink(item)"
          :editing="true"
          @remove="removeItem(item.id)"
        >
          <template #header-drag>
            <div
              class="vuedash__drag-handle"
              @pointerdown="(e) => onDragStart(item.id, e)"
            ></div>
          </template>
          <component :is="getWidgetComponent(item)" />
        </DashboardWidget>

        <!-- Resize handles — both bottom corners -->
        <div
          class="vuedash__resize-handle vuedash__resize-handle--se"
          @pointerdown="(e) => onResizeStart(item.id, 'se', e)"
          @pointermove="onResizeMove"
          @pointerup="onResizeEnd"
        >
          <span class="vuedash__grip-dots">⠿</span>
        </div>
        <div
          class="vuedash__resize-handle vuedash__resize-handle--sw"
          @pointerdown="(e) => onResizeStart(item.id, 'sw', e)"
          @pointermove="onResizeMove"
          @pointerup="onResizeEnd"
        >
          <span class="vuedash__grip-dots">⠿</span>
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
              @click="onAddWidget(def.type)"
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
import { ref, reactive, nextTick, onMounted, onUnmounted, type Component, markRaw } from 'vue'
import { useVueDash } from '@/composables/useVueDash'
import type { VueDashItem } from '@/composables/useVueDash'
import { getWidgetDef } from '@/composables/useVueDash'
import { createLogger } from '@/utils/logger'
import DashboardWidget from '@/components/dashboard/DashboardWidget.vue'
import WidgetTasksPriority from '@/components/dashboard/WidgetTasksPriority.vue'
import WidgetCountdowns from '@/components/dashboard/WidgetCountdowns.vue'
import WidgetEvents from '@/components/dashboard/WidgetEvents.vue'
import WidgetHabits from '@/components/dashboard/WidgetHabits.vue'
import WidgetBooks from '@/components/dashboard/WidgetBooks.vue'
import WidgetArticles from '@/components/dashboard/WidgetArticles.vue'
import WidgetMoneyWasted from '@/components/dashboard/WidgetMoneyWasted.vue'
import WidgetAutoTasks from '@/components/dashboard/WidgetAutoTasks.vue'
import WidgetDurations from '@/components/dashboard/WidgetDurations.vue'

const logger = createLogger('VueDashView')

const {
  items,
  dragState,
  resizeState,
  gridStyle,
  availableWidgets,
  itemStyle,
  loadLayout,
  addItem,
  removeItem,
  startDrag,
  handleDragMove,
  handleDrop,
  dragTransform,
  startResize,
  handleResizeMove,
  handleResizeEnd,
  resizeStyle,
  startAutoRefresh,
  stopAutoRefresh,
} = useVueDash()

const gridRef = ref<HTMLElement>()
const showWidgetPicker = ref(false)

// FLIP animation state — per-item transform + size overrides during snap
const snapAnimations = reactive<Record<string, { transform?: string; width?: string; height?: string; transition?: string }>>({})

// Template ref map — stores references to each item element by ID
const itemRefs = new Map<string, HTMLElement>()
function setItemRef(id: string, el: HTMLElement | null) {
  if (el) itemRefs.set(id, el)
  else itemRefs.delete(id)
}

// Exaggerated slow snap — 800ms for now so you can see it clearly
const SNAP_DURATION = 1600

async function flipAnimate(itemId: string, beforeRect: DOMRect, beforeWidth?: number, beforeHeight?: number) {
  // Wait for Vue to render the new grid position
  await nextTick()

  const el = itemRefs.get(itemId)
  if (!el) return

  // L: Where did it end up?
  const afterRect = el.getBoundingClientRect()

  // I: Calculate the delta and apply as transform (element visually stays at old position)
  const deltaX = beforeRect.left - afterRect.left
  const deltaY = beforeRect.top - afterRect.top

  const style: Record<string, string> = {
    transform: `translate(${deltaX}px, ${deltaY}px)`,
    transition: 'none',
  }

  // For resize: also invert the size change
  if (beforeWidth !== undefined && beforeHeight !== undefined) {
    style.width = `${beforeWidth}px`
    style.height = `${beforeHeight}px`
    style.justifySelf = 'start'
    style.alignSelf = 'start'
  }

  snapAnimations[itemId] = style

  // Force a layout read so the browser registers the inverted position
  // eslint-disable-next-line @typescript-eslint/no-unused-expressions
  el.offsetHeight

  // P: Now animate to the final position (and size if resizing)
  requestAnimationFrame(() => {
    const playStyle: Record<string, string> = {
      transform: 'translate(0, 0)',
      transition: `all ${SNAP_DURATION}ms cubic-bezier(0.16, 1, 0.3, 1)`,
    }

    if (beforeWidth !== undefined) {
      // Animate to the grid cell's actual size (can't transition to 'auto')
      playStyle.width = `${afterRect.width}px`
      playStyle.height = `${afterRect.height}px`
      playStyle.justifySelf = 'start'
      playStyle.alignSelf = 'start'
    }

    snapAnimations[itemId] = playStyle

    setTimeout(() => {
      // Clean up — remove overrides so grid controls sizing again
      delete snapAnimations[itemId]
    }, SNAP_DURATION + 50)
  })
}

const widgetComponents: Record<string, Component> = {
  'tasks-priority': markRaw(WidgetTasksPriority),
  countdowns: markRaw(WidgetCountdowns),
  events: markRaw(WidgetEvents),
  habits: markRaw(WidgetHabits),
  books: markRaw(WidgetBooks),
  articles: markRaw(WidgetArticles),
  'money-wasted': markRaw(WidgetMoneyWasted),
  autotasks: markRaw(WidgetAutoTasks),
  durations: markRaw(WidgetDurations),
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

function getWidgetTitle(item: VueDashItem): string {
  return getWidgetDef(item.widgetType)?.name ?? 'Unknown'
}

function getWidgetIcon(item: VueDashItem): string {
  return getWidgetDef(item.widgetType)?.icon ?? 'fa-solid fa-question'
}

function getWidgetLink(item: VueDashItem): string {
  return linkMap[item.widgetType] ?? '/'
}

function getWidgetComponent(item: VueDashItem): Component | null {
  return widgetComponents[item.widgetType] ?? null
}

function onDragStart(itemId: string, event: PointerEvent) {
  if (!gridRef.value) return
  const itemEl = (event.target as HTMLElement).closest('.vuedash__item') as HTMLElement
  if (!itemEl) return
  startDrag(itemId, event, itemEl, gridRef.value)
}

function onPointerMove(event: PointerEvent) {
  if (!gridRef.value) return
  if (dragState.value) {
    handleDragMove(event, gridRef.value)
  }
}

function onPointerUp() {
  // Handle resize end from global listener (pointer capture may prevent element-level events)
  if (resizeState.value) {
    onResizeEnd()
    return
  }
  if (!dragState.value) return
  const itemId = dragState.value.itemId
  const el = itemRefs.get(itemId)
  if (!el) {
    handleDrop()
    return
  }

  // F: Snapshot current position (where user released)
  const beforeRect = el.getBoundingClientRect()

  // Update grid data + clear drag state
  handleDrop()

  // FLIP animate from drag position to grid cell
  flipAnimate(itemId, beforeRect)
}

function onResizeStart(itemId: string, direction: 'se' | 'sw', event: PointerEvent) {
  if (!gridRef.value) return
  const itemEl = (event.target as HTMLElement).closest('.vuedash__item') as HTMLElement
  if (!itemEl) return
  startResize(itemId, direction, event, itemEl, gridRef.value)
}

function onResizeMove(event: PointerEvent) {
  if (!gridRef.value) return
  handleResizeMove(event, gridRef.value)
}

function onResizeEnd() {
  if (!resizeState.value) return
  const rs = resizeState.value
  const itemId = rs.itemId
  const el = itemRefs.get(itemId)
  if (!el) {
    handleResizeEnd()
    return
  }

  // F: Snapshot current pixel position + size WHILE still absolute-positioned
  const beforeRect = el.getBoundingClientRect()
  const beforeWidth = rs.currentWidth
  const beforeHeight = rs.currentHeight

  // Update grid data + clear resize state (element jumps to grid cell)
  handleResizeEnd()

  // FLIP animate from resize position/size to grid cell
  flipAnimate(itemId, beforeRect, beforeWidth, beforeHeight)
}

function onAddWidget(type: string) {
  addItem(type)
  showWidgetPicker.value = false
}

function refreshAllWidgets() {
  logger.info('widgets_refreshed')
}

onMounted(() => {
  items.value = loadLayout()
  startAutoRefresh(refreshAllWidgets, 180_000)
  window.addEventListener('pointermove', onPointerMove)
  window.addEventListener('pointerup', onPointerUp)
  logger.info('vuedash_initialized', { widgetCount: items.value.length })
})

onUnmounted(() => {
  stopAutoRefresh()
  window.removeEventListener('pointermove', onPointerMove)
  window.removeEventListener('pointerup', onPointerUp)
})
</script>

<style scoped>
.vuedash {
  max-width: 100%;
}

.vuedash__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-s);
}

.vuedash__title {
  font-size: var(--fs-600);
  color: var(--clr-accent);
  margin: 0;
  text-shadow:
    0 0 8px var(--clr-accent),
    var(--deep-3d-text-shadow);
}

.vuedash__grid {
  position: relative;
  border-radius: var(--button-border-radius, 12px);
  padding: var(--space-3xs);
  background:
    radial-gradient(circle at 20% 50%, var(--clr-black-trans-200) 0%, transparent 50%),
    radial-gradient(circle at 80% 50%, var(--clr-black-trans-200) 0%, transparent 50%), var(--clr-primary--darker);
}

.vuedash__item {
  position: relative;
  z-index: 2;
  transition: opacity 0.2s ease;
  touch-action: none;
}

.vuedash__item--dragging {
  z-index: 100;
  opacity: 0.9;
  transition: none;
}

.vuedash__item--snapping {
  z-index: 50;
}

.vuedash__item--dragging .dashboard-widget {
  box-shadow:
    var(--floating-box),
    0 0 15px var(--clr-accent);
  transition: box-shadow 0.15s ease;
}

/* Drag handle — invisible overlay covering the entire header */
.vuedash__drag-handle {
  position: absolute;
  inset: 0;
  cursor: grab;
  z-index: 5;
}

.vuedash__drag-handle:active {
  cursor: grabbing;
}

/* Resize handles — subtle grip dots in both bottom corners */
.vuedash__resize-handle {
  position: absolute;
  bottom: 4px;
  width: 1.5rem;
  height: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  touch-action: none;
  opacity: 0.3;
  transition: opacity 0.15s ease;
}

.vuedash__item:hover .vuedash__resize-handle {
  opacity: 0.7;
}

.vuedash__resize-handle:hover {
  opacity: 1 !important;
}

.vuedash__resize-handle--se {
  right: 4px;
  cursor: se-resize;
}

.vuedash__resize-handle--sw {
  left: 4px;
  cursor: sw-resize;
}

.vuedash__grip-dots {
  color: var(--clr-gray-500);
  font-size: 1.25rem;
  line-height: 1;
  transition: color 0.15s ease;
}

.vuedash__resize-handle:hover .vuedash__grip-dots {
  color: var(--clr-accent);
}
</style>

<style>
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
