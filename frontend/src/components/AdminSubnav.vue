<template>
  <div class="grid grid--one-column grid--tight">
    <div class="admin-subnav">
      <RouterLink
        to="/admin"
        class="admin-subnav__link"
        :class="{ 'admin-subnav__link--active': active === 'system' }"
      >
        System Health
      </RouterLink>
      <RouterLink
        to="/admin/scheduler"
        class="admin-subnav__link"
        :class="{ 'admin-subnav__link--active': active === 'scheduler' }"
      >
        Scheduler
      </RouterLink>
      <RouterLink
        to="/admin/users"
        class="admin-subnav__link"
        :class="{ 'admin-subnav__link--active': active === 'users' }"
      >
        Users
      </RouterLink>
      <RouterLink
        to="/admin/config"
        class="admin-subnav__link"
        :class="{ 'admin-subnav__link--active': active === 'config' }"
      >
        Config
      </RouterLink>
      <RouterLink
        to="/admin/smoke"
        class="admin-subnav__link"
        :class="{ 'admin-subnav__link--active': active === 'smoke' }"
      >
        Smoke Tests
      </RouterLink>
      <RouterLink
        to="/autotasks"
        class="admin-subnav__link"
        :class="{ 'admin-subnav__link--active': active === 'autotasks' }"
      >
        AutoTasks
      </RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  active: 'system' | 'scheduler' | 'users' | 'config' | 'smoke' | 'autotasks'
}>()
</script>

<style scoped>
.admin-subnav {
  display: flex;
  gap: var(--space-s);
  padding-bottom: var(--space-xs);
  border-bottom: 2px solid var(--clr-gray-700);
}

.admin-subnav__link {
  color: var(--clr-gray-400);
  text-decoration: none;
  padding: var(--space-3xs) var(--space-xs);
  font-size: var(--fs-400);
  transition: color 0.2s;
}

.admin-subnav__link:hover {
  color: var(--clr-primary-400);
}

.admin-subnav__link--active {
  color: var(--clr-primary-300);
  border-bottom: 2px solid var(--clr-primary-400);
}
</style>
