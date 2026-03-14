<template>
  <!-- Collapsed tab — visible when sidebar is closed -->
  <Transition name="tab">
    <div
      v-if="!open"
      class="sidebar-tab"
    >
      <div
        class="button-sidebar-tab"
        tabindex="0"
        @click="$emit('toggle')"
        @keydown.enter="$emit('toggle')"
      >
        <div class="button-sidebar-tab__text">
          <span class="fa-solid fa-chevron-right"></span>
        </div>
      </div>
    </div>
  </Transition>

  <!-- Sidebar -->
  <Transition name="sidebar">
    <aside
      v-show="open"
      class="sidebar"
    >
      <div class="sidebar__header">
        <a
          href="/"
          class="sidebar__title"
        >
          iChrisBirch
        </a>
      </div>
      <div
        class="button-sidebar-toggle"
        tabindex="0"
        @click="$emit('toggle')"
        @keydown.enter="$emit('toggle')"
      >
        <div class="button-sidebar-toggle__text">
          <span class="fa-solid fa-chevron-left"></span>
        </div>
      </div>
      <nav class="sidebar__nav">
        <template
          v-for="link in mainLinks"
          :key="link.to"
        >
          <RouterLink
            v-if="link.migrated"
            :to="link.to"
            class="nav-link"
            :class="{ 'nav-link--active': isActive(link) }"
          >
            <i :class="link.icon"></i>
            <span class="nav-link__label">{{ link.label }}</span>
          </RouterLink>
          <a
            v-else
            :href="link.to"
            class="nav-link"
          >
            <i :class="link.icon"></i>
            <span class="nav-link__label">{{ link.label }}</span>
          </a>
        </template>
      </nav>
      <div class="sidebar__footer">
        <template
          v-for="link in footerLinks"
          :key="link.to"
        >
          <RouterLink
            v-if="link.migrated"
            :to="link.to"
            class="nav-link"
            :class="{ 'nav-link--active': isActive(link) }"
          >
            <i :class="link.icon"></i>
            <span class="nav-link__label">{{ link.label }}</span>
          </RouterLink>
          <a
            v-else
            :href="link.to"
            class="nav-link"
          >
            <i :class="link.icon"></i>
            <span class="nav-link__label">{{ link.label }}</span>
          </a>
        </template>
      </div>
    </aside>
  </Transition>
</template>

<script setup lang="ts">
import { RouterLink, useRoute } from 'vue-router'

defineProps<{
  open: boolean
}>()

defineEmits<{
  toggle: []
}>()

interface NavLink {
  to: string
  label: string
  icon: string
  migrated: boolean
  activeNames?: string[]
}

const route = useRoute()

const mainLinks: NavLink[] = [
  { to: '/', label: 'Home', icon: 'fa-solid fa-house', migrated: false },
  {
    to: '/articles',
    label: 'Articles',
    icon: 'fa-solid fa-newspaper',
    migrated: true,
    activeNames: ['articles', 'article-insights', 'article-bulk-import'],
  },
  { to: '/autotasks', label: 'AutoTasks', icon: 'fa-solid fa-robot', migrated: true },
  { to: '/books', label: 'Books', icon: 'fa-solid fa-book', migrated: true },
  { to: '/box-packing', label: 'Box Packing', icon: 'fa-solid fa-box', migrated: false },
  { to: '/countdowns', label: 'Countdowns', icon: 'fa-solid fa-hourglass-half', migrated: true },
  { to: '/durations', label: 'Durations', icon: 'fa-solid fa-clock-rotate-left', migrated: true },
  { to: '/events', label: 'Events', icon: 'fa-solid fa-calendar', migrated: true },
  { to: '/habits', label: 'Habits', icon: 'fa-solid fa-repeat', migrated: false },
  { to: '/money-wasted', label: 'Money Wasted', icon: 'fa-solid fa-money-bill-wave', migrated: true },
  {
    to: '/tasks',
    label: 'Tasks',
    icon: 'fa-solid fa-list-check',
    migrated: false,
    activeNames: ['tasks', 'tasks-priority', 'tasks-completed'],
  },
]

const footerLinks: NavLink[] = [{ to: '/admin', label: 'Admin', icon: 'fa-solid fa-gear', migrated: false }]

function isActive(link: NavLink): boolean {
  if (link.activeNames) {
    return link.activeNames.includes(route.name as string)
  }
  return route.path === link.to
}
</script>

<style scoped>
.sidebar {
  width: 220px;
  background-color: var(--clr-primary--darker);
  border-right: 1px solid var(--clr-gray-800);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
}

.sidebar__header {
  padding: var(--space-m) var(--space-s);
}

.sidebar__title {
  font-size: var(--fs-600);
  color: var(--clr-accent);
  font-weight: 700;
  text-decoration: none;
  text-shadow: var(--text-glow);
}

.sidebar__nav {
  padding: var(--space-xs);
  display: flex;
  flex-direction: column;
  gap: var(--space-3xs);
  flex: 1;
  overflow-y: auto;
}

.sidebar__footer {
  padding: var(--space-xs);
  border-top: 1px solid var(--clr-gray-800);
}

.nav-link {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-3xs) var(--space-xs);
  border-radius: 4px;
  color: var(--clr-gray-100);
  font-weight: 500;
  text-decoration: none;
  transition: all 0.15s ease;
  font-size: var(--fs-300);
}

.nav-link i {
  width: 1.25em;
  text-align: center;
  flex-shrink: 0;
}

.nav-link:hover {
  background-color: var(--clr-primary--lighter);
  color: var(--clr-text);
}

.nav-link--active {
  background-color: var(--clr-primary--lighter);
  color: var(--clr-accent);
}

/* Collapsed tab — bevel button on the left edge */
.sidebar-tab {
  position: fixed;
  top: var(--space-m);
  left: var(--space-xs);
  z-index: 100;
}

/* Sidebar slide transition */
.sidebar-enter-active,
.sidebar-leave-active {
  transition: transform 0.25s ease;
}

.sidebar-enter-from,
.sidebar-leave-to {
  transform: translateX(-100%);
}

/* Tab fade transition */
.tab-enter-active,
.tab-leave-active {
  transition: opacity 0.2s ease 0.15s;
}

.tab-enter-from,
.tab-leave-to {
  opacity: 0;
}
</style>
