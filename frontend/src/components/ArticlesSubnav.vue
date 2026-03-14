<template>
  <div class="grid grid--one-column grid--tight">
    <div class="articles-subnav">
      <RouterLink
        to="/articles"
        class="articles-subnav__link"
        :class="{ 'articles-subnav__link--active': active === 'articles' }"
      >
        All Articles
      </RouterLink>
      <RouterLink
        to="/articles/bulk-import"
        class="articles-subnav__link"
        :class="{ 'articles-subnav__link--active': active === 'bulk-import' }"
      >
        Bulk Import
      </RouterLink>
      <RouterLink
        to="/articles/insights"
        class="articles-subnav__link"
        :class="{ 'articles-subnav__link--active': active === 'insights' }"
      >
        Insights
      </RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  active: 'articles' | 'bulk-import' | 'insights'
}>()
</script>

<style scoped>
.articles-subnav {
  display: flex;
  gap: var(--space-s);
  padding-bottom: var(--space-xs);
  border-bottom: 2px solid var(--clr-gray-700);
}

.articles-subnav__link {
  color: var(--clr-gray-400);
  text-decoration: none;
  padding: var(--space-3xs) var(--space-xs);
  font-size: var(--fs-400);
  transition: color 0.2s;
}

.articles-subnav__link:hover {
  color: var(--clr-primary-400);
}

.articles-subnav__link--active {
  color: var(--clr-primary-300);
  border-bottom: 2px solid var(--clr-primary-400);
}
</style>
