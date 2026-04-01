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
      <div class="sidebar__issue">
        <SubmitIssueButton @click="$emit('open-issue')" />
      </div>
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
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { allMainLinks, DEFAULT_SIDEBAR_ORDER, type NavLink } from '@/components/sidebarLinks'
import SubmitIssueButton from '@/components/SubmitIssueButton.vue'

defineProps<{
  open: boolean
}>()

defineEmits<{
  toggle: []
  'open-issue': []
}>()

const route = useRoute()
const auth = useAuthStore()

const mainLinks = computed(() => {
  const order = (auth.preferences?.sidebar_order as string[] | undefined) ?? DEFAULT_SIDEBAR_ORDER
  const linkMap = new Map(allMainLinks.map((link) => [link.to, link]))
  const sorted: NavLink[] = []
  for (const path of order) {
    const link = linkMap.get(path)
    if (link) {
      sorted.push(link)
      linkMap.delete(path)
    }
  }
  for (const link of linkMap.values()) {
    sorted.push(link)
  }
  return sorted
})

const footerLinks: NavLink[] = [
  {
    to: '/profile',
    label: 'Profile',
    icon: 'fa-solid fa-user',
    migrated: true,
    activeNames: ['profile', 'profile-settings'],
  },
  {
    to: '/admin',
    label: 'Admin',
    icon: 'fa-solid fa-gear',
    migrated: true,
    activeNames: ['admin', 'admin-scheduler', 'admin-users', 'admin-config', 'admin-design'],
  },
]

function isActive(link: NavLink): boolean {
  if (link.activeNames) {
    return link.activeNames.includes(route.name as string)
  }
  return route.path === link.to
}
</script>

<style lang="scss" scoped>
@use 'components/buttons';
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
  overflow: visible;
}

.sidebar__issue {
  padding: var(--space-m) 0;
  display: flex;
  justify-content: center;
}

.sidebar__footer {
  padding: var(--space-xs);
  border-top: 1px solid var(--clr-gray-800);
}

.nav-link {
  @include buttons.neu-button($active-class: '--active', $hover-transform: scale(1.2), $pressed-transform: scale(0.99));
  transform-origin: center left;
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-3xs) var(--space-xs);
  font-weight: 500;
  text-decoration: none;
  font-size: var(--fs-300);
}

.nav-link i {
  width: 1.25em;
  text-align: center;
  flex-shrink: 0;
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
