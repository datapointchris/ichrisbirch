<template>
  <div class="grid grid--one-column grid--tight">
    <div class="coffee-subnav">
      <RouterLink
        to="/coffee/shops"
        class="coffee-subnav__link"
        :class="{ 'coffee-subnav__link--active': active === 'shops' }"
        data-testid="coffee-subnav-shops"
      >
        <i class="fa-solid fa-mug-hot"></i>
        Shops
      </RouterLink>
      <RouterLink
        to="/coffee/beans"
        class="coffee-subnav__link"
        :class="{ 'coffee-subnav__link--active': active === 'beans' }"
        data-testid="coffee-subnav-beans"
      >
        <i class="fa-solid fa-seedling"></i>
        Beans
      </RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  active: 'shops' | 'beans'
}>()
</script>

<style scoped>
.coffee-subnav {
  display: flex;
  gap: var(--space-s);
  padding-bottom: var(--space-xs);
  border-bottom: 2px solid var(--clr-gray-700);
}

.coffee-subnav__link {
  color: var(--clr-gray-400);
  text-decoration: none;
  padding: var(--space-3xs) var(--space-xs);
  font-size: var(--fs-400);
  transition: color 0.2s;
  display: flex;
  align-items: center;
  gap: var(--space-2xs);
}

.coffee-subnav__link:hover {
  color: var(--clr-accent-light);
}

.coffee-subnav__link--active {
  color: var(--clr-accent-light);
  border-bottom: 2px solid var(--clr-accent-light);
  margin-bottom: -2px;
}
</style>
