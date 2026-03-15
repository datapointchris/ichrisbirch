<template>
  <div class="widget-list">
    <div
      v-if="store.loading"
      class="widget-loading"
    >
      Loading...
    </div>
    <template v-else>
      <div class="widget-stats">
        <span class="widget-stats__total">${{ store.totalWasted.toFixed(2) }}</span>
        <span>total wasted</span>
      </div>
      <div
        v-for="item in recentItems"
        :key="item.id"
        class="widget-list__item"
      >
        <span class="widget-list__name">{{ item.item }}</span>
        <span class="widget-list__meta">${{ item.amount.toFixed(2) }}</span>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useMoneyWastedStore } from '@/stores/moneyWasted'

const store = useMoneyWastedStore()

const recentItems = computed(() => store.sortedItems.slice(0, 6))

onMounted(() => {
  if (store.items.length === 0) store.fetchAll()
})
</script>

<style scoped>
.widget-stats {
  display: flex;
  align-items: baseline;
  gap: var(--space-xs);
  padding-bottom: var(--space-2xs);
  border-bottom: 1px solid var(--clr-gray-800);
  margin-bottom: var(--space-2xs);
  color: var(--clr-gray-400);
  font-size: var(--fs-200);
}

.widget-stats__total {
  font-size: var(--fs-500);
  font-weight: 700;
  color: var(--clr-accent--red);
}
</style>
