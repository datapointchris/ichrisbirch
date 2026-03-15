<template>
  <div class="grid grid--one-column grid--tight">
    <div class="box-packing-subnav">
      <RouterLink
        to="/box-packing"
        class="box-packing-subnav__link"
        :class="{ 'box-packing-subnav__link--active': active === 'all' }"
      >
        All Boxes
      </RouterLink>
      <RouterLink
        to="/box-packing/orphans"
        class="box-packing-subnav__link"
        :class="{ 'box-packing-subnav__link--active': active === 'orphans' }"
      >
        Orphans
      </RouterLink>
      <RouterLink
        to="/box-packing/search"
        class="box-packing-subnav__link"
        :class="{ 'box-packing-subnav__link--active': active === 'search' }"
      >
        Search
      </RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  active: 'all' | 'detail' | 'orphans' | 'search'
}>()
</script>

<style scoped>
.box-packing-subnav {
  display: flex;
  gap: var(--space-s);
  padding-bottom: var(--space-xs);
  border-bottom: 2px solid var(--clr-gray-700);
}

.box-packing-subnav__link {
  color: var(--clr-gray-400);
  text-decoration: none;
  padding: var(--space-3xs) var(--space-xs);
  font-size: var(--fs-400);
  transition: color 0.2s;
}

.box-packing-subnav__link:hover {
  color: var(--clr-primary-400);
}

.box-packing-subnav__link--active {
  color: var(--clr-primary-300);
  border-bottom: 2px solid var(--clr-primary-400);
}
</style>
