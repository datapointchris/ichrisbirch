<template>
  <div class="grid grid--one-column grid--tight">
    <div class="habits-subnav">
      <RouterLink
        to="/habits"
        class="habits-subnav__link"
        :class="{ 'habits-subnav__link--active': active === 'daily' }"
      >
        Daily Habits
      </RouterLink>
      <RouterLink
        to="/habits/completed"
        class="habits-subnav__link"
        :class="{ 'habits-subnav__link--active': active === 'completed' }"
      >
        Completed
      </RouterLink>
      <RouterLink
        to="/habits/manage"
        class="habits-subnav__link"
        :class="{ 'habits-subnav__link--active': active === 'manage' }"
      >
        Manage
      </RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  active: 'daily' | 'completed' | 'manage'
}>()
</script>

<style scoped>
.habits-subnav {
  display: flex;
  gap: var(--space-s);
  padding-bottom: var(--space-xs);
  border-bottom: 2px solid var(--clr-gray-700);
}

.habits-subnav__link {
  color: var(--clr-gray-400);
  text-decoration: none;
  padding: var(--space-3xs) var(--space-xs);
  font-size: var(--fs-400);
  transition: color 0.2s;
}

.habits-subnav__link:hover {
  color: var(--clr-primary-400);
}

.habits-subnav__link--active {
  color: var(--clr-primary-300);
  border-bottom: 2px solid var(--clr-primary-400);
}
</style>
