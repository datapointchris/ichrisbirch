<template>
  <div class="grid grid--one-column grid--tight">
    <div class="profile-subnav">
      <RouterLink
        to="/profile"
        class="profile-subnav__link"
        :class="{ 'profile-subnav__link--active': active === 'profile' }"
      >
        Profile
      </RouterLink>
      <RouterLink
        to="/profile/settings"
        class="profile-subnav__link"
        :class="{ 'profile-subnav__link--active': active === 'settings' }"
      >
        Settings
      </RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  active: 'profile' | 'settings'
}>()
</script>

<style scoped>
.profile-subnav {
  display: flex;
  gap: var(--space-s);
  padding-bottom: var(--space-xs);
  border-bottom: 2px solid var(--clr-gray-700);
}

.profile-subnav__link {
  color: var(--clr-gray-400);
  text-decoration: none;
  padding: var(--space-3xs) var(--space-xs);
  font-size: var(--fs-400);
  transition: color 0.2s;
}

.profile-subnav__link:hover {
  color: var(--clr-primary-400);
}

.profile-subnav__link--active {
  color: var(--clr-primary-300);
  border-bottom: 2px solid var(--clr-primary-400);
}
</style>
