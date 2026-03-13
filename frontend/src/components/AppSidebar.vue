<template>
  <Transition name="sidebar">
    <aside
      v-show="open"
      class="sidebar"
    >
      <div class="sidebar__header">
        <RouterLink
          to="/"
          class="sidebar__title"
        >
          iChrisBirch
        </RouterLink>
      </div>
      <nav class="sidebar__nav">
        <RouterLink
          v-for="link in mainLinks"
          :key="link.to"
          :to="link.to"
          class="nav-link"
          :class="{ 'nav-link--active': isActive(link) }"
        >
          <i :class="link.icon"></i>
          <span class="nav-link__label">{{ link.label }}</span>
        </RouterLink>
      </nav>
      <div class="sidebar__footer">
        <RouterLink
          v-for="link in footerLinks"
          :key="link.to"
          :to="link.to"
          class="nav-link"
          :class="{ 'nav-link--active': isActive(link) }"
        >
          <i :class="link.icon"></i>
          <span class="nav-link__label">{{ link.label }}</span>
        </RouterLink>
      </div>
    </aside>
  </Transition>
</template>

<script setup lang="ts">
import { RouterLink, useRoute } from 'vue-router'

defineProps<{
  open: boolean
}>()

interface NavLink {
  to: string
  label: string
  icon: string
  activeNames?: string[]
}

const route = useRoute()

const mainLinks: NavLink[] = [
  { to: '/', label: 'Home', icon: 'fa-solid fa-house' },
  { to: '/articles', label: 'Articles', icon: 'fa-solid fa-newspaper' },
  { to: '/autotasks', label: 'AutoTasks', icon: 'fa-solid fa-robot' },
  { to: '/books', label: 'Books', icon: 'fa-solid fa-book' },
  { to: '/box-packing', label: 'Box Packing', icon: 'fa-solid fa-box' },
  { to: '/countdowns', label: 'Countdowns', icon: 'fa-solid fa-hourglass-half' },
  { to: '/events', label: 'Events', icon: 'fa-solid fa-calendar' },
  { to: '/habits', label: 'Habits', icon: 'fa-solid fa-repeat' },
  { to: '/money-wasted', label: 'Money Wasted', icon: 'fa-solid fa-money-bill-wave' },
  { to: '/tasks', label: 'Tasks', icon: 'fa-solid fa-list-check', activeNames: ['tasks', 'tasks-priority', 'tasks-completed'] },
]

const footerLinks: NavLink[] = [
  { to: '/admin', label: 'Admin', icon: 'fa-solid fa-gear' },
]

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
  border-bottom: 1px solid var(--clr-gray-800);
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

/* Slide transition */
.sidebar-enter-active,
.sidebar-leave-active {
  transition: transform 0.25s ease;
}

.sidebar-enter-from,
.sidebar-leave-to {
  transform: translateX(-100%);
}
</style>
